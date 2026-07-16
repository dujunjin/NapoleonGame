using System;
using System.Collections.Generic;
using System.Linq;

namespace NapoleonGame.Domain
{
    public sealed class GameEngine
    {
        public const int StartingHeadquartersHealth = 20;
        public const int SupportCapacity = 4;
        public const int FrontlineCapacity = 5;
        public const int CreditCap = 12;
        public const int HandLimit = 9;
        public const int RoundLimit = 30;

        private readonly CardCatalog _catalog;
        private readonly List<GameEvent> _events = new List<GameEvent>();
        private StableRandom _random;
        private int _nextCardInstanceId;
        private int _nextUnitId;

        public GameEngine(CardCatalog catalog)
        {
            _catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
        }

        public GameState State { get; private set; }

        public CommandResult StartMatch(Faction humanFaction, Faction enemyFaction, int seed)
        {
            _events.Clear();
            _random = new StableRandom(seed);
            _nextCardInstanceId = 1;
            _nextUnitId = 1;

            var playerOne = new PlayerState(0, _catalog.GetFaction(humanFaction), true);
            var playerTwo = new PlayerState(1, _catalog.GetFaction(enemyFaction), false);
            State = new GameState(playerOne, playerTwo, seed);

            BuildDeck(playerOne, _catalog.GetFaction(humanFaction));
            BuildDeck(playerTwo, _catalog.GetFaction(enemyFaction));
            Shuffle(playerOne.MutableDeck);
            Shuffle(playerTwo.MutableDeck);
            DrawCards(playerOne, 4);
            DrawCards(playerTwo, 5);
            BeginTurn(playerOne, false);

            Emit(GameEventType.MatchStarted, 0, string.Empty, string.Empty, seed,
                playerOne.Name + " 对阵 " + playerTwo.Name + " · 种子 " + seed);
            return CommandResult.Success(_events.ToArray());
        }

        public CommandResult Execute(GameCommand command)
        {
            if (State == null)
            {
                return CommandResult.Failure("对局尚未开始");
            }

            if (command == null)
            {
                return CommandResult.Failure("无效命令");
            }

            if (State.IsEnded)
            {
                return CommandResult.Failure("对局已经结束");
            }

            if (command.PlayerId != State.ActivePlayerId)
            {
                return CommandResult.Failure("尚未轮到该玩家");
            }

            _events.Clear();
            string failure;
            if (command is DeployCommand deploy)
            {
                failure = ExecuteDeploy(deploy);
            }
            else if (command is MoveCommand move)
            {
                failure = ExecuteMove(move);
            }
            else if (command is AttackCommand attack)
            {
                failure = ExecuteAttack(attack);
            }
            else if (command is PlayEventCommand playEvent)
            {
                failure = ExecuteEvent(playEvent);
            }
            else if (command is CommanderCommand commander)
            {
                failure = ExecuteCommander(commander);
            }
            else if (command is EndTurnCommand endTurn)
            {
                failure = ExecuteEndTurn(endTurn);
            }
            else
            {
                failure = "未知命令";
            }

            if (!string.IsNullOrEmpty(failure))
            {
                _events.Clear();
                return CommandResult.Failure(failure);
            }

            ResolveMatchEnd();
            return CommandResult.Success(_events.ToArray());
        }

        public IReadOnlyList<GameCommand> GetLegalActions(int playerId)
        {
            var actions = new List<GameCommand>();
            if (State == null || State.IsEnded || playerId != State.ActivePlayerId)
            {
                return actions;
            }

            var player = State.Players[playerId];
            foreach (var card in player.Hand)
            {
                if (card.Definition.DeployCost > player.CurrentCredits)
                {
                    continue;
                }

                if (card.Definition.CardType == CardType.Unit)
                {
                    for (var slot = 0; slot < SupportCapacity; slot++)
                    {
                        if (State.GetSupportUnit(playerId, slot) == null)
                        {
                            actions.Add(new DeployCommand(playerId, card.InstanceId, slot));
                        }
                    }
                }
                else
                {
                    AddLegalEventActions(actions, playerId, card);
                }
            }

            foreach (var unit in State.GetUnits(playerId).ToArray())
            {
                if (CanOperate(unit, player))
                {
                    if (unit.Zone == BattleZone.Support && CanEnterFrontline(playerId))
                    {
                        for (var slot = 0; slot < FrontlineCapacity; slot++)
                        {
                            if (State.GetFrontlineUnit(slot) == null)
                            {
                                actions.Add(new MoveCommand(playerId, unit.Id, slot));
                            }
                        }
                    }

                    foreach (var target in GetLegalUnitTargets(unit))
                    {
                        actions.Add(new AttackCommand(playerId, unit.Id, TargetKind.Unit, target.Id));
                    }

                    if (CanAttackHeadquarters(unit))
                    {
                        actions.Add(new AttackCommand(playerId, unit.Id, TargetKind.Headquarters));
                    }
                }
            }

            AddCommanderActions(actions, playerId);
            actions.Add(new EndTurnCommand(playerId));
            return actions;
        }

        public int GetEffectiveAttack(UnitState unit)
        {
            var attack = unit.Definition.Attack + unit.AttackModifier;
            if (unit.IsShaken)
            {
                attack -= 1;
            }

            if (unit.Zone == BattleZone.Frontline && unit.HasKeyword("阿尔科莱精神"))
            {
                attack += 2;
            }

            if (unit.Definition.Subfaction == "imperial_guard")
            {
                attack += Math.Min(3, State.GetUnits(unit.OwnerId).Count(other => other.Definition.Subfaction == "imperial_guard"));
            }

            if (unit.Definition.UnitType == UnitType.Cavalry)
            {
                var hasArtilleryLink = State.GetUnits(unit.OwnerId).Any(other =>
                    other.Slot == unit.Slot && other.HasKeyword("军团联动"));
                if (hasArtilleryLink)
                {
                    attack += 1;
                }
            }

            var intimidation = State.GetUnits(1 - unit.OwnerId).Count(other =>
                other.Slot == unit.Slot && other.HasKeyword("死神威慑"));
            attack -= intimidation;

            if (unit.Definition.Name == "反冲击突击队" && unit.CurrentHealth < unit.MaxHealth)
            {
                attack += 1;
            }

            if (unit.HasKeyword("Same-line Threshold"))
            {
                var zoneCount = State.GetUnits(unit.OwnerId).Count(other => other.Zone == unit.Zone);
                if (zoneCount >= 3)
                {
                    attack += 1;
                }
            }

            return Math.Max(0, attack);
        }

        private void BuildDeck(PlayerState player, FactionCatalog faction)
        {
            foreach (var definition in faction.Cards)
            {
                for (var copy = 0; copy < definition.Quantity; copy++)
                {
                    player.MutableDeck.Add(new CardInstance("c" + _nextCardInstanceId++, definition));
                }
            }
        }

        private void Shuffle(List<CardInstance> cards)
        {
            for (var index = cards.Count - 1; index > 0; index--)
            {
                var swap = _random.Next(index + 1);
                var temporary = cards[index];
                cards[index] = cards[swap];
                cards[swap] = temporary;
            }
        }

        private void DrawCards(PlayerState player, int count)
        {
            for (var draw = 0; draw < count; draw++)
            {
                if (player.MutableHand.Count >= HandLimit)
                {
                    return;
                }

                if (player.MutableDeck.Count == 0)
                {
                    player.FatigueDamage += 1;
                    player.HeadquartersHealth -= player.FatigueDamage;
                    Emit(GameEventType.Damage, player.Id, "fatigue", "hq-" + player.Id, player.FatigueDamage,
                        player.Name + " 疲劳：HQ -" + player.FatigueDamage);
                    continue;
                }

                var card = player.MutableDeck[0];
                player.MutableDeck.RemoveAt(0);
                player.MutableHand.Add(card);
                Emit(GameEventType.CardDrawn, player.Id, card.InstanceId, string.Empty, 0,
                    player.Name + " 抽取一张牌");
            }
        }

        private void BeginTurn(PlayerState player, bool drawCard)
        {
            var boost = player.PendingCreditBoost;
            player.PendingCreditBoost = 0;
            player.MaxCredits = Math.Min(CreditCap, player.MaxCredits + 1 + boost);
            player.CurrentCredits = player.MaxCredits;
            foreach (var unit in State.GetUnits(player.Id))
            {
                unit.IsExhausted = false;
                unit.DeployedThisTurn = false;
                unit.HasUsedVolley = false;
                unit.OnWoundedExhausted = false;
                unit.ShakenAtTurnStart = unit.IsShaken;
            }

            if (drawCard)
            {
                DrawCards(player, 1);
            }

            Emit(GameEventType.TurnStarted, player.Id, string.Empty, string.Empty, State.Round,
                "第 " + State.Round + " 轮 · " + player.Name + " 行动");
            Emit(GameEventType.CreditsChanged, player.Id, string.Empty, string.Empty, player.CurrentCredits,
                "军令 " + player.CurrentCredits + "/" + player.MaxCredits);
        }

        private string ExecuteDeploy(DeployCommand command)
        {
            var player = State.Players[command.PlayerId];
            var card = player.Hand.FirstOrDefault(item => item.InstanceId == command.CardInstanceId);
            if (card == null || card.Definition.CardType != CardType.Unit)
            {
                return "手牌中没有该单位";
            }

            if (!GameState.IsSupportSlot(command.SupportSlot) || State.GetSupportUnit(command.PlayerId, command.SupportSlot) != null)
            {
                return "支援线槽位不可用";
            }

            if (player.CurrentCredits < card.Definition.DeployCost)
            {
                return "军令不足";
            }

            player.CurrentCredits -= card.Definition.DeployCost;
            player.MutableHand.Remove(card);
            var unit = new UnitState("u" + _nextUnitId++, command.PlayerId, card.Definition, BattleZone.Support, command.SupportSlot)
            {
                DeployedThisTurn = true,
                IsExhausted = !card.Definition.HasKeyword("冲锋")
            };
            State.SetSupportUnit(command.PlayerId, command.SupportSlot, unit);
            ApplyDeployEffects(unit);

            Emit(GameEventType.CardDeployed, command.PlayerId, card.InstanceId, unit.Id, card.Definition.DeployCost,
                player.Name + " 部署「" + card.Definition.Name + "」");
            Emit(GameEventType.CreditsChanged, command.PlayerId, string.Empty, string.Empty, player.CurrentCredits,
                "剩余军令 " + player.CurrentCredits);
            return string.Empty;
        }

        private void ApplyDeployEffects(UnitState unit)
        {
            foreach (var keyword in unit.Definition.Keywords)
            {
                if (keyword.StartsWith("自残", StringComparison.Ordinal) &&
                    int.TryParse(keyword.Substring(2), out var selfDamage))
                {
                    State.Players[unit.OwnerId].HeadquartersHealth -= selfDamage;
                    Emit(GameEventType.Damage, unit.OwnerId, unit.Id, "hq-" + unit.OwnerId, selfDamage,
                        unit.Definition.Name + "：己方HQ -" + selfDamage);
                }
            }

            if (unit.HasKeyword("光环+1攻"))
            {
                foreach (var friendly in State.GetUnits(unit.OwnerId).Where(other => other != unit))
                {
                    friendly.AttackModifier += 1;
                }
            }

            if (unit.HasKeyword("光环+1血"))
            {
                foreach (var friendly in State.GetUnits(unit.OwnerId).Where(other => other != unit))
                {
                    friendly.HealthModifier += 1;
                    friendly.CurrentHealth += 1;
                }
            }
        }

        private string ExecuteMove(MoveCommand command)
        {
            var player = State.Players[command.PlayerId];
            var unit = State.FindUnit(command.UnitId);
            if (unit == null || unit.OwnerId != command.PlayerId || unit.Zone != BattleZone.Support)
            {
                return "该单位不在己方支援线";
            }

            var operationFailure = GetOperationFailure(unit, player);
            if (!string.IsNullOrEmpty(operationFailure))
            {
                return operationFailure;
            }

            if (!CanEnterFrontline(command.PlayerId))
            {
                return "敌方控制前线，必须先清除前线单位";
            }

            if (!GameState.IsFrontlineSlot(command.FrontlineSlot) || State.GetFrontlineUnit(command.FrontlineSlot) != null)
            {
                return "前线槽位不可用";
            }

            player.CurrentCredits -= unit.Definition.OperationCost;
            State.SetSupportUnit(command.PlayerId, unit.Slot, null);
            unit.Zone = BattleZone.Frontline;
            unit.Slot = command.FrontlineSlot;
            unit.IsExhausted = true;
            if (unit.Definition.Name == "撤退中的炮兵队")
            {
                unit.AttackModifier += 1;
            }
            State.SetFrontlineUnit(command.FrontlineSlot, unit);
            Emit(GameEventType.UnitMoved, command.PlayerId, unit.Id, "front-" + command.FrontlineSlot,
                unit.Definition.OperationCost, unit.Definition.Name + " 进入前线");
            return string.Empty;
        }

        private string ExecuteAttack(AttackCommand command)
        {
            var player = State.Players[command.PlayerId];
            var attacker = State.FindUnit(command.AttackerId);
            if (attacker == null || attacker.OwnerId != command.PlayerId)
            {
                return "攻击单位无效";
            }

            var operationFailure = GetOperationFailure(attacker, player);
            if (!string.IsNullOrEmpty(operationFailure))
            {
                return operationFailure;
            }

            UnitState defender = null;
            if (command.TargetKind == TargetKind.Unit)
            {
                defender = State.FindUnit(command.TargetUnitId);
                if (defender == null || !GetLegalUnitTargets(attacker).Contains(defender))
                {
                    return "该单位不是合法目标";
                }
            }
            else if (!CanAttackHeadquarters(attacker))
            {
                return "尚未打开HQ攻击通路";
            }

            player.CurrentCredits -= attacker.Definition.OperationCost;
            attacker.IsExhausted = true;
            Emit(GameEventType.AttackStarted, command.PlayerId, attacker.Id,
                defender == null ? "hq-" + (1 - command.PlayerId) : defender.Id, 0,
                attacker.Definition.Name + " 发起攻击");

            if (defender == null)
            {
                var damage = GetEffectiveAttack(attacker);
                State.Players[1 - command.PlayerId].HeadquartersHealth -= damage;
                Emit(GameEventType.Damage, command.PlayerId, attacker.Id, "hq-" + (1 - command.PlayerId), damage,
                    "HQ 受到 " + damage + " 点伤害");
            }
            else
            {
                ResolveUnitCombat(attacker, defender);
            }

            if (!attacker.IsDead && attacker.HasKeyword("熔岩战术") && attacker.Zone == BattleZone.Frontline)
            {
                RetreatToFirstSupport(attacker, false);
            }

            return string.Empty;
        }

        private void ResolveUnitCombat(UnitState attacker, UnitState defender)
        {
            var attack = GetEffectiveAttack(attacker);
            var defenderHealthBefore = defender.CurrentHealth;

            if (attacker.HasKeyword("齐射") && !attacker.HasUsedVolley)
            {
                attacker.HasUsedVolley = true;
                DealDamage(defender, 1, attacker, true);
            }

            if (!defender.IsDead)
            {
                var defenderDamage = CalculateDamage(attacker, defender, attack);
                DealDamage(defender, defenderDamage, attacker, true);
            }

            if (!defender.IsDead && !attacker.HasKeyword("远程"))
            {
                var counter = defender.Definition.UnitType == UnitType.Artillery
                    ? defender.Definition.Attack / 2
                    : defender.Definition.Attack;
                DealDamage(attacker, Math.Max(0, counter), defender, false);
            }

            var overflow = Math.Max(0, -defender.CurrentHealth);
            if (defender.IsDead && attacker.HasKeyword("突破") && overflow > 0)
            {
                State.Players[defender.OwnerId].HeadquartersHealth -= overflow;
                Emit(GameEventType.Damage, attacker.OwnerId, attacker.Id, "hq-" + defender.OwnerId, overflow,
                    "突破：HQ -" + overflow);
            }

            if (defender.IsDead)
            {
                DestroyUnit(defender, attacker);
            }

            if (attacker.IsDead)
            {
                DestroyUnit(attacker, defender);
            }

            if (defenderHealthBefore > 0 && defender.CurrentHealth < defender.MaxHealth && defender.HasKeyword("On Wounded"))
            {
                defender.OnWoundedExhausted = true;
            }
        }

        private int CalculateDamage(UnitState attacker, UnitState defender, int effectiveAttack)
        {
            var isInfantryTarget = defender.Definition.UnitType == UnitType.Infantry || defender.Definition.UnitType == UnitType.Guard;
            if (attacker.Definition.UnitType == UnitType.Cavalry && isInfantryTarget)
            {
                if (defender.HasKeyword("结阵") && !attacker.HasKeyword("突破"))
                {
                    return Math.Max(1, effectiveAttack / 2);
                }

                if (!defender.HasKeyword("结阵"))
                {
                    return effectiveAttack * 2;
                }
            }

            if (attacker.Definition.UnitType == UnitType.Artillery && isInfantryTarget)
            {
                return effectiveAttack + (defender.HasKeyword("结阵") ? 2 : 1);
            }

            return effectiveAttack;
        }

        private void DealDamage(UnitState target, int damage, UnitState source, bool allowEvade)
        {
            if (damage <= 0 || target.IsDead)
            {
                return;
            }

            if (allowEvade && target.HasKeyword("闪避") && !target.HasUsedEvade &&
                source.Definition.UnitType != UnitType.Artillery)
            {
                target.HasUsedEvade = true;
                Emit(GameEventType.Damage, source.OwnerId, source.Id, target.Id, 0,
                    target.Definition.Name + " 闪避了攻击");
                return;
            }

            target.CurrentHealth -= damage;
            Emit(GameEventType.Damage, source.OwnerId, source.Id, target.Id, damage,
                target.Definition.Name + " -" + damage + " HP");
            if (!target.IsDead && damage >= 2 && target.CurrentHealth * 2 <= target.MaxHealth && !target.IsShaken)
            {
                target.IsShaken = true;
                Emit(GameEventType.UnitShaken, target.OwnerId, target.Id, target.Id, 0,
                    target.Definition.Name + " 陷入动摇");
            }
        }

        private void DestroyUnit(UnitState unit, UnitState source)
        {
            if (unit.Zone == BattleZone.Support)
            {
                State.SetSupportUnit(unit.OwnerId, unit.Slot, null);
            }
            else
            {
                State.SetFrontlineUnit(unit.Slot, null);
            }

            var owner = State.Players[unit.OwnerId];
            if (unit.HasKeyword("焦土补给"))
            {
                owner.PendingCreditBoost += 1;
            }

            if (owner.CossackRefundPending && unit.Definition.Subfaction == "cossack")
            {
                owner.CossackRefundPending = false;
                owner.CurrentCredits = Math.Min(owner.MaxCredits, owner.CurrentCredits + unit.Definition.OperationCost);
            }

            Emit(GameEventType.UnitDestroyed, source.OwnerId, source.Id, unit.Id, 0,
                unit.Definition.Name + " 被击毁");
        }

        private string ExecuteEvent(PlayEventCommand command)
        {
            var player = State.Players[command.PlayerId];
            var card = player.Hand.FirstOrDefault(item => item.InstanceId == command.CardInstanceId);
            if (card == null || card.Definition.CardType != CardType.Event)
            {
                return "手牌中没有该事件";
            }

            if (player.CurrentCredits < card.Definition.DeployCost)
            {
                return "军令不足";
            }

            var validation = ValidateEventTarget(command.PlayerId, card.Definition.EventEffect, command.TargetUnitId);
            if (!string.IsNullOrEmpty(validation))
            {
                return validation;
            }

            player.CurrentCredits -= card.Definition.DeployCost;
            player.MutableHand.Remove(card);
            player.MutableDiscard.Add(card);
            ResolveEventEffect(command.PlayerId, card.Definition.EventEffect, command.TargetUnitId);
            Emit(GameEventType.EventPlayed, command.PlayerId, card.InstanceId, command.TargetUnitId,
                card.Definition.DeployCost, player.Name + " 打出「" + card.Definition.Name + "」");
            return string.Empty;
        }

        private string ValidateEventTarget(int playerId, string effect, string targetId)
        {
            var target = State.FindUnit(targetId);
            if (EffectNeedsFriendlyInfantry(effect))
            {
                return target != null && target.OwnerId == playerId && target.Definition.UnitType == UnitType.Infantry
                    ? string.Empty
                    : "需要选择己方步兵";
            }

            if (effect == "fortify_target_INF_GUARD+0+2_guard")
            {
                return target != null && target.OwnerId == playerId &&
                    (target.Definition.UnitType == UnitType.Infantry || target.Definition.UnitType == UnitType.Guard)
                    ? string.Empty
                    : "需要选择己方步兵或近卫";
            }

            if (effect == "advance_friendly_one_no_attack")
            {
                return target != null && target.OwnerId == playerId && target.Zone == BattleZone.Support &&
                       !target.IsShaken && CanEnterFrontline(playerId) && FirstEmptyFrontlineSlot() >= 0
                    ? string.Empty
                    : "需要可进入前线的未动摇支援单位";
            }

            if (effect == "retreat_friendly_heal2_hq1")
            {
                return target != null && target.OwnerId == playerId && target.Zone == BattleZone.Frontline && FirstEmptySupportSlot(playerId) >= 0
                    ? string.Empty
                    : "需要可撤回的己方前线单位";
            }

            if (effect == "buff_imperial_guard_deploy_sequence")
            {
                return target != null && target.OwnerId == playerId && target.Definition.Subfaction == "imperial_guard"
                    ? string.Empty
                    : "需要选择帝国近卫";
            }

            if (effect == "buff_landwehr_sequence")
            {
                return target != null && target.OwnerId == playerId && target.Definition.Subfaction == "landwehr"
                    ? string.Empty
                    : "需要选择国土后备军";
            }

            return string.Empty;
        }

        private void ResolveEventEffect(int playerId, string effect, string targetId)
        {
            var player = State.Players[playerId];
            var target = State.FindUnit(targetId);
            switch (effect)
            {
                case "buff_target_INF+1+2":
                    BuffAndHeal(target, 1, 2, 2);
                    break;
                case "advance_friendly_one_no_attack":
                    MoveToFrontlineFree(target);
                    break;
                case "fortify_target_INF_GUARD+0+2_guard":
                    BuffAndHeal(target, 0, 2, 2);
                    target.AddKeyword("守卫");
                    break;
                case "draw1_buff_target_INF+1+1":
                    DrawCards(player, 1);
                    BuffAndHeal(target, 1, 1, 1);
                    break;
                case "buff_all_friendly_CAV_GUARD+1":
                    foreach (var unit in State.GetUnits(playerId).Where(unit =>
                                 unit.Definition.UnitType == UnitType.Cavalry || unit.Definition.UnitType == UnitType.Guard))
                    {
                        unit.AttackModifier += 1;
                    }
                    break;
                case "retreat_friendly_heal2_hq1":
                    RetreatToFirstSupport(target, true);
                    player.HeadquartersHealth -= 1;
                    break;
                case "self_hq1_damage_enemy_skirmish1":
                    player.HeadquartersHealth -= 1;
                    foreach (var enemy in State.GetFrontlineUnits().Where(unit => unit.OwnerId != playerId).ToArray())
                    {
                        DealDamage(enemy, 1, CreateEventSource(playerId, effect), false);
                        if (enemy.IsDead)
                        {
                            DestroyUnit(enemy, CreateEventSource(playerId, effect));
                        }
                    }
                    break;
                case "weather_fog_artillery-1":
                    ModifyAllAttack(UnitType.Artillery, -1);
                    break;
                case "weather_mud_cavalry-1":
                    ModifyAllAttack(UnitType.Cavalry, -1);
                    break;
                case "weather_winter_all_damage1":
                    foreach (var unit in State.GetUnits(0).Concat(State.GetUnits(1)).ToArray())
                    {
                        var source = CreateEventSource(playerId, effect);
                        DealDamage(unit, 1, source, false);
                        if (unit.IsDead)
                        {
                            DestroyUnit(unit, source);
                        }
                    }
                    break;
                case "buff_imperial_guard_deploy_sequence":
                case "buff_landwehr_sequence":
                    BuffAndHeal(target, 1, 1, 1);
                    DrawCards(player, 1);
                    break;
                case "buff_cossack_death_extend":
                    player.CossackRefundPending = true;
                    break;
            }
        }

        private UnitState CreateEventSource(int playerId, string effect)
        {
            var definition = new CardDefinition("event-source", effect, State.Players[playerId].Faction,
                CardType.Unit, UnitType.Artillery, 0, 0, 0, 1, Array.Empty<string>(), string.Empty,
                string.Empty, 0, string.Empty, string.Empty);
            return new UnitState("event-" + State.EventSequence, playerId, definition, BattleZone.Support, 0);
        }

        private string ExecuteCommander(CommanderCommand command)
        {
            var player = State.Players[command.PlayerId];
            if (player.CommanderUsed)
            {
                return "指挥官能力已经使用";
            }

            var target = State.FindUnit(command.TargetUnitId);
            if (target == null || target.OwnerId != command.PlayerId)
            {
                return "需要选择己方单位";
            }

            if (player.CommanderId == "napoleon")
            {
                if (target.Zone != BattleZone.Support || !CanEnterFrontline(command.PlayerId) || FirstEmptyFrontlineSlot() < 0)
                {
                    return "拿破仑需要选择可进入前线的支援单位";
                }
                MoveToFrontlineFree(target);
                target.IsExhausted = false;
            }
            else if (player.CommanderId == "blucher")
            {
                if (target.CurrentHealth >= target.MaxHealth)
                {
                    return "布吕歇尔需要选择受伤单位";
                }
                target.AttackModifier += 1;
                target.IsExhausted = false;
            }
            else if (player.CommanderId == "kutuzov")
            {
                if (target.Zone != BattleZone.Frontline || FirstEmptySupportSlot(command.PlayerId) < 0)
                {
                    return "库图佐夫需要选择可撤回的前线单位";
                }
                RetreatToFirstSupport(target, true);
                player.HeadquartersHealth = Math.Min(StartingHeadquartersHealth, player.HeadquartersHealth + 1);
            }

            player.CommanderUsed = true;
            Emit(GameEventType.CommanderUsed, command.PlayerId, player.CommanderId, target.Id, 0,
                player.CommanderName + " 发动指挥官能力");
            return string.Empty;
        }

        private string ExecuteEndTurn(EndTurnCommand command)
        {
            var player = State.Players[command.PlayerId];
            foreach (var unit in State.GetUnits(player.Id))
            {
                if (unit.ShakenAtTurnStart && unit.IsShaken)
                {
                    unit.IsShaken = false;
                    unit.ShakenAtTurnStart = false;
                    Emit(GameEventType.UnitRecovered, player.Id, unit.Id, unit.Id, 0,
                        unit.Definition.Name + " 完成重整");
                }
            }

            Emit(GameEventType.TurnEnded, player.Id, string.Empty, string.Empty, State.Round,
                player.Name + " 结束行动");
            if (player.Id == 1)
            {
                State.Round += 1;
            }

            if (State.Round > RoundLimit)
            {
                EndByRoundLimit();
                return string.Empty;
            }

            State.ActivePlayerId = 1 - player.Id;
            BeginTurn(State.Players[State.ActivePlayerId], true);
            return string.Empty;
        }

        private void AddLegalEventActions(List<GameCommand> actions, int playerId, CardInstance card)
        {
            var effect = card.Definition.EventEffect;
            if (!EventRequiresTarget(effect))
            {
                actions.Add(new PlayEventCommand(playerId, card.InstanceId));
                return;
            }

            foreach (var unit in State.GetUnits(playerId))
            {
                if (string.IsNullOrEmpty(ValidateEventTarget(playerId, effect, unit.Id)))
                {
                    actions.Add(new PlayEventCommand(playerId, card.InstanceId, unit.Id));
                }
            }
        }

        private void AddCommanderActions(List<GameCommand> actions, int playerId)
        {
            var player = State.Players[playerId];
            if (player.CommanderUsed)
            {
                return;
            }

            foreach (var unit in State.GetUnits(playerId))
            {
                if (player.CommanderId == "napoleon" && unit.Zone == BattleZone.Support && CanEnterFrontline(playerId) && FirstEmptyFrontlineSlot() >= 0)
                {
                    actions.Add(new CommanderCommand(playerId, unit.Id));
                }
                else if (player.CommanderId == "blucher" && unit.CurrentHealth < unit.MaxHealth)
                {
                    actions.Add(new CommanderCommand(playerId, unit.Id));
                }
                else if (player.CommanderId == "kutuzov" && unit.Zone == BattleZone.Frontline && FirstEmptySupportSlot(playerId) >= 0)
                {
                    actions.Add(new CommanderCommand(playerId, unit.Id));
                }
            }
        }

        private IReadOnlyList<UnitState> GetLegalUnitTargets(UnitState attacker)
        {
            var enemyId = 1 - attacker.OwnerId;
            var targets = new List<UnitState>();
            var enemyFrontline = State.GetFrontlineUnits().Where(unit => unit.OwnerId == enemyId).ToList();

            if (attacker.Zone == BattleZone.Support)
            {
                targets.AddRange(enemyFrontline);
                if (attacker.HasKeyword("远程") || attacker.HasKeyword("侧翼迂回"))
                {
                    targets.AddRange(State.GetSupportUnits(enemyId));
                }
            }
            else if (State.FrontlineOwner == attacker.OwnerId)
            {
                targets.AddRange(State.GetSupportUnits(enemyId));
            }

            var guards = targets.Where(target => target.HasKeyword("守卫")).ToList();
            return guards.Count > 0 ? guards : targets;
        }

        private bool CanAttackHeadquarters(UnitState attacker)
        {
            if (!CanOperate(attacker, State.Players[attacker.OwnerId]))
            {
                return false;
            }

            if (attacker.Zone == BattleZone.Frontline && State.FrontlineOwner == attacker.OwnerId)
            {
                return true;
            }

            if (attacker.Zone == BattleZone.Support && attacker.HasKeyword("远程"))
            {
                var enemyId = 1 - attacker.OwnerId;
                return !State.GetUnits(enemyId).Any();
            }

            return false;
        }

        private bool CanEnterFrontline(int playerId)
        {
            return State.FrontlineOwner < 0 || State.FrontlineOwner == playerId;
        }

        private bool CanOperate(UnitState unit, PlayerState player)
        {
            return !unit.IsDead && !unit.IsExhausted && !unit.IsShaken &&
                   player.CurrentCredits >= unit.Definition.OperationCost;
        }

        private string GetOperationFailure(UnitState unit, PlayerState player)
        {
            if (unit.IsDead)
            {
                return "单位已经被击毁";
            }
            if (unit.IsShaken)
            {
                return "动摇单位本回合不能行动";
            }
            if (unit.IsExhausted)
            {
                return "单位本回合已经行动";
            }
            if (player.CurrentCredits < unit.Definition.OperationCost)
            {
                return "行动军令不足";
            }
            return string.Empty;
        }

        private void MoveToFrontlineFree(UnitState unit)
        {
            var slot = FirstEmptyFrontlineSlot();
            State.SetSupportUnit(unit.OwnerId, unit.Slot, null);
            unit.Zone = BattleZone.Frontline;
            unit.Slot = slot;
            unit.IsExhausted = true;
            State.SetFrontlineUnit(slot, unit);
            Emit(GameEventType.UnitMoved, unit.OwnerId, unit.Id, "front-" + slot, 0,
                unit.Definition.Name + " 进入前线");
        }

        private void RetreatToFirstSupport(UnitState unit, bool heal)
        {
            var slot = FirstEmptySupportSlot(unit.OwnerId);
            if (slot < 0)
            {
                return;
            }

            State.SetFrontlineUnit(unit.Slot, null);
            unit.Zone = BattleZone.Support;
            unit.Slot = slot;
            unit.IsExhausted = true;
            if (heal)
            {
                unit.CurrentHealth = Math.Min(unit.MaxHealth, unit.CurrentHealth + 2);
            }
            State.SetSupportUnit(unit.OwnerId, slot, unit);
            Emit(GameEventType.UnitMoved, unit.OwnerId, unit.Id, "support-" + unit.OwnerId + "-" + slot, 0,
                unit.Definition.Name + " 撤回支援线");
        }

        private int FirstEmptySupportSlot(int playerId)
        {
            for (var slot = 0; slot < SupportCapacity; slot++)
            {
                if (State.GetSupportUnit(playerId, slot) == null)
                {
                    return slot;
                }
            }
            return -1;
        }

        private int FirstEmptyFrontlineSlot()
        {
            for (var slot = 0; slot < FrontlineCapacity; slot++)
            {
                if (State.GetFrontlineUnit(slot) == null)
                {
                    return slot;
                }
            }
            return -1;
        }

        private void BuffAndHeal(UnitState unit, int attack, int health, int heal)
        {
            unit.AttackModifier += attack;
            unit.HealthModifier += health;
            unit.CurrentHealth = Math.Min(unit.MaxHealth, unit.CurrentHealth + health + heal);
        }

        private void ModifyAllAttack(UnitType type, int amount)
        {
            foreach (var unit in State.GetUnits(0).Concat(State.GetUnits(1)).Where(unit => unit.Definition.UnitType == type))
            {
                unit.AttackModifier += amount;
            }
        }

        private static bool EffectNeedsFriendlyInfantry(string effect)
        {
            return effect == "buff_target_INF+1+2" || effect == "draw1_buff_target_INF+1+1";
        }

        private static bool EventRequiresTarget(string effect)
        {
            return EffectNeedsFriendlyInfantry(effect) ||
                   effect == "advance_friendly_one_no_attack" ||
                   effect == "fortify_target_INF_GUARD+0+2_guard" ||
                   effect == "retreat_friendly_heal2_hq1" ||
                   effect == "buff_imperial_guard_deploy_sequence" ||
                   effect == "buff_landwehr_sequence";
        }

        private void ResolveMatchEnd()
        {
            if (State.IsEnded)
            {
                return;
            }

            var firstDead = State.Players[0].HeadquartersHealth <= 0;
            var secondDead = State.Players[1].HeadquartersHealth <= 0;
            if (!firstDead && !secondDead)
            {
                return;
            }

            State.IsEnded = true;
            State.EndReason = firstDead && secondDead ? MatchEndReason.Draw : MatchEndReason.HeadquartersDestroyed;
            State.WinnerId = firstDead == secondDead ? -1 : firstDead ? 1 : 0;
            Emit(GameEventType.MatchEnded, State.WinnerId, string.Empty, string.Empty, State.Round,
                State.WinnerId < 0 ? "双方HQ同时被摧毁" : State.Players[State.WinnerId].Name + " 获胜");
        }

        private void EndByRoundLimit()
        {
            var first = State.Players[0].HeadquartersHealth;
            var second = State.Players[1].HeadquartersHealth;
            State.IsEnded = true;
            State.EndReason = first == second ? MatchEndReason.Draw : MatchEndReason.RoundLimit;
            State.WinnerId = first == second ? -1 : first > second ? 0 : 1;
            Emit(GameEventType.MatchEnded, State.WinnerId, string.Empty, string.Empty, State.Round,
                State.WinnerId < 0 ? "轮次上限：平局" : "轮次上限：" + State.Players[State.WinnerId].Name + " 获胜");
        }

        private void Emit(GameEventType type, int playerId, string sourceId, string targetId, int amount, string message)
        {
            State.EventSequence += 1;
            _events.Add(new GameEvent(State.EventSequence, type, playerId, sourceId, targetId, amount, message));
        }
    }
}
