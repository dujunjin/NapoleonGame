using System;
using System.Collections.Generic;
using System.Linq;
using NapoleonGame.Domain;
using UnityEngine;
using UnityEngine.UIElements;

namespace NapoleonGame.Runtime
{
    public sealed class BattleScreenController
    {
        private enum SourceKind
        {
            Card,
            Unit,
            Commander
        }

        private readonly VisualElement _root;
        private readonly VisualElement _battleSurface;
        private readonly VisualElement _dragLayer;
        private readonly VisualElement _enemyHeadquarters;
        private readonly VisualElement _playerHeadquarters;
        private readonly VisualElement[] _enemySupportSlots;
        private readonly VisualElement[] _playerSupportSlots;
        private readonly VisualElement[] _frontlineSlots;
        private readonly ScrollView _hand;
        private readonly ScrollView _eventLog;
        private readonly Button _endTurnButton;
        private readonly Button _commanderButton;
        private readonly Toggle _reducedMotionToggle;
        private readonly VisualElement _setupOverlay;
        private readonly VisualElement _resultOverlay;
        private readonly DropdownField _playerFactionField;
        private readonly DropdownField _enemyFactionField;
        private readonly IntegerField _seedField;
        private readonly Label _toast;
        private readonly Label _turnHint;
        private readonly Action<GameCommand> _executeCommand;
        private readonly Action<Faction, Faction, int> _startMatch;
        private readonly Action _requestRematch;

        private readonly Dictionary<string, VisualElement> _unitViews = new Dictionary<string, VisualElement>();
        private readonly Dictionary<string, VisualElement> _cardViews = new Dictionary<string, VisualElement>();
        private readonly Dictionary<VisualElement, GameCommand> _dropTargets = new Dictionary<VisualElement, GameCommand>();
        private readonly Dictionary<string, Vector2> _lastKnownUnitCenters = new Dictionary<string, Vector2>();
        private readonly List<VisualElement> _previewBadges = new List<VisualElement>();
        private IReadOnlyList<GameCommand> _legalActions = Array.Empty<GameCommand>();
        private GameEngine _engine;
        private VisualElement _selectedElement;
        private string _selectedSourceId;
        private SourceKind _selectedSourceKind;
        private int _pointerId = -1;
        private Vector2 _pointerStart;
        private VisualElement _pointerSourceElement;
        private string _pointerSourceId;
        private SourceKind _pointerSourceKind;
        private bool _dragging;
        private bool _suppressNextClick;
        private VisualElement _dragGhost;
        private AttackArrowElement _attackArrow;
        private VisualElement _magnetTarget;
        private GameCommand _pendingTargetCommand;
        private bool _inputLocked;
        private int _toastVersion;

        public BattleScreenController(
            VisualElement root,
            Action<GameCommand> executeCommand,
            Action<Faction, Faction, int> startMatch,
            Action requestRematch)
        {
            _root = root ?? throw new ArgumentNullException(nameof(root));
            _executeCommand = executeCommand ?? throw new ArgumentNullException(nameof(executeCommand));
            _startMatch = startMatch ?? throw new ArgumentNullException(nameof(startMatch));
            _requestRematch = requestRematch ?? throw new ArgumentNullException(nameof(requestRematch));

            _battleSurface = Required<VisualElement>("battle-surface");
            _dragLayer = Required<VisualElement>("drag-layer");
            _enemyHeadquarters = Required<VisualElement>("enemy-hq");
            _playerHeadquarters = Required<VisualElement>("player-hq");
            _hand = Required<ScrollView>("hand");
            _eventLog = Required<ScrollView>("event-log");
            _endTurnButton = Required<Button>("end-turn-button");
            _commanderButton = Required<Button>("commander-button");
            _reducedMotionToggle = Required<Toggle>("reduced-motion");
            _setupOverlay = Required<VisualElement>("setup-overlay");
            _resultOverlay = Required<VisualElement>("result-overlay");
            _playerFactionField = Required<DropdownField>("player-faction-field");
            _enemyFactionField = Required<DropdownField>("enemy-faction-field");
            _seedField = Required<IntegerField>("seed-field");
            _toast = Required<Label>("toast");
            _turnHint = Required<Label>("turn-hint");

            _enemySupportSlots = Enumerable.Range(0, GameEngine.SupportCapacity)
                .Select(index => Required<VisualElement>("enemy-support-" + index)).ToArray();
            _playerSupportSlots = Enumerable.Range(0, GameEngine.SupportCapacity)
                .Select(index => Required<VisualElement>("player-support-" + index)).ToArray();
            _frontlineSlots = Enumerable.Range(0, GameEngine.FrontlineCapacity)
                .Select(index => Required<VisualElement>("frontline-" + index)).ToArray();

            ConfigureStaticInteraction();
            ConfigureSetupOverlay();
            ApplyBattlefieldArt();
        }

        public bool ReducedMotion => _reducedMotionToggle.value;

        public void Render(GameEngine engine)
        {
            _engine = engine ?? throw new ArgumentNullException(nameof(engine));
            var previousCenters = new Dictionary<string, Vector2>();
            foreach (var pair in _unitViews)
            {
                if (pair.Value.panel == null)
                {
                    continue;
                }
                previousCenters[pair.Key] = pair.Value.worldBound.center;
                _lastKnownUnitCenters[pair.Key] = pair.Value.worldBound.center;
            }
            ClearSelection();
            _unitViews.Clear();
            _cardViews.Clear();

            var state = engine.State;
            var player = state.Players[0];
            var enemy = state.Players[1];
            _legalActions = !state.IsEnded && state.ActivePlayerId == 0
                ? engine.GetLegalActions(0)
                : Array.Empty<GameCommand>();

            Required<Label>("enemy-name").text = enemy.Name + " · " + enemy.CommanderName;
            Required<Label>("player-name").text = player.Name + " · " + player.CommanderName;
            Required<Label>("enemy-counts").text = "手牌 " + enemy.Hand.Count + " · 牌库 " + enemy.Deck.Count;
            Required<Label>("player-counts").text = "牌库 " + player.Deck.Count + " · 弃牌 " + player.Discard.Count;
            Required<Label>("round-label").text = "第 " + state.Round + " 回合";
            Required<Label>("enemy-resource").text = "指挥点 " + enemy.CurrentCredits + " / " + enemy.MaxCredits;
            Required<Label>("player-resource").text = "指挥点 " + player.CurrentCredits + " / " + player.MaxCredits;
            Required<Label>("enemy-hq-health").text = Math.Max(0, enemy.HeadquartersHealth) + " / " + GameEngine.StartingHeadquartersHealth;
            Required<Label>("player-hq-health").text = Math.Max(0, player.HeadquartersHealth) + " / " + GameEngine.StartingHeadquartersHealth;
            SetHealthBar(Required<VisualElement>("enemy-health-fill"), enemy.HeadquartersHealth);
            SetHealthBar(Required<VisualElement>("player-health-fill"), player.HeadquartersHealth);

            var owner = state.FrontlineOwner;
            Required<Label>("frontline-status").text = owner < 0
                ? "前线：无人控制"
                : owner == 0 ? "前线：我方控制" : "前线：敌方控制";

            for (var slot = 0; slot < GameEngine.SupportCapacity; slot++)
            {
                PopulateSlot(_enemySupportSlots[slot], state.GetSupportUnit(1, slot));
                PopulateSlot(_playerSupportSlots[slot], state.GetSupportUnit(0, slot));
            }

            for (var slot = 0; slot < GameEngine.FrontlineCapacity; slot++)
            {
                PopulateSlot(_frontlineSlots[slot], state.GetFrontlineUnit(slot));
            }

            _hand.Clear();
            foreach (var card in player.Hand)
            {
                var view = CreateCardView(card);
                _hand.Add(view);
                _cardViews[card.InstanceId] = view;
            }

            var isHumanTurn = !state.IsEnded && state.ActivePlayerId == 0 && !_inputLocked;
            _endTurnButton.SetEnabled(isHumanTurn && _legalActions.OfType<EndTurnCommand>().Any());
            _commanderButton.SetEnabled(isHumanTurn && _legalActions.OfType<CommanderCommand>().Any());
            _turnHint.text = state.IsEnded
                ? "战役已经结束。"
                : state.ActivePlayerId == 0
                    ? "拖动手牌部署；拖动己方单位推进或攻击。"
                    : "敌军正在下达命令……";

            if (state.IsEnded)
            {
                ShowResult(state);
            }

            if (previousCenters.Count > 0 && !ReducedMotion)
            {
                _root.schedule.Execute(() => AnimateBoardReflow(previousCenters)).ExecuteLater(1);
            }
        }

        public void SetInputLocked(bool locked)
        {
            _inputLocked = locked;
            ClearSelection();
            if (_engine == null || _engine.State == null)
            {
                return;
            }

            var isHumanTurn = !locked && !_engine.State.IsEnded && _engine.State.ActivePlayerId == 0;
            _endTurnButton.SetEnabled(isHumanTurn && _legalActions.OfType<EndTurnCommand>().Any());
            _commanderButton.SetEnabled(isHumanTurn && _legalActions.OfType<CommanderCommand>().Any());
        }

        public void ClearLog()
        {
            _eventLog.Clear();
        }

        public void AppendEvent(GameEvent gameEvent)
        {
            if (gameEvent == null || string.IsNullOrEmpty(gameEvent.Message))
            {
                return;
            }

            var entry = new Label(gameEvent.Message);
            entry.AddToClassList("event-entry");
            _eventLog.Add(entry);
            while (_eventLog.childCount > 18)
            {
                _eventLog.RemoveAt(0);
            }
            _eventLog.schedule.Execute(() => _eventLog.ScrollTo(entry));
        }

        public float AnimateEvent(GameEvent gameEvent)
        {
            AppendEvent(gameEvent);
            if (ReducedMotion)
            {
                return 0f;
            }

            switch (gameEvent.Type)
            {
                case GameEventType.CardDeployed:
                case GameEventType.UnitMoved:
                    var arrivingId = gameEvent.Type == GameEventType.CardDeployed
                        ? gameEvent.TargetId
                        : gameEvent.SourceId;
                    if (_unitViews.TryGetValue(arrivingId, out var arriving))
                    {
                        PulseClass(arriving, "anim-deploy", 20);
                    }
                    return 0.11f;

                case GameEventType.AttackStarted:
                    ShowAttack(gameEvent.SourceId, gameEvent.TargetId);
                    return 0.16f;

                case GameEventType.Damage:
                    ShowDamage(gameEvent.TargetId, gameEvent.Amount);
                    return 0.18f;

                case GameEventType.UnitShaken:
                    if (_unitViews.TryGetValue(gameEvent.TargetId, out var shaken))
                    {
                        PulseClass(shaken, "anim-hit", 150);
                    }
                    return 0.13f;

                case GameEventType.UnitDestroyed:
                    if (_unitViews.TryGetValue(gameEvent.TargetId, out var destroyed))
                    {
                        destroyed.AddToClassList("anim-destroy");
                    }
                    ShowDestruction(gameEvent.TargetId);
                    return 0.16f;

                case GameEventType.TurnStarted:
                    ShowTurnBanner(gameEvent.PlayerId, gameEvent.Amount);
                    return 0.18f;

                default:
                    return 0.02f;
            }
        }

        public void ShowToast(string message)
        {
            _toastVersion += 1;
            var version = _toastVersion;
            _toast.text = message;
            _toast.RemoveFromClassList("hidden-overlay");
            _toast.schedule.Execute(() =>
            {
                if (version == _toastVersion)
                {
                    _toast.AddToClassList("hidden-overlay");
                }
            }).ExecuteLater(1800);
        }

        public void ShowSetup(Faction playerFaction, Faction enemyFaction, int seed)
        {
            _playerFactionField.value = FactionName(playerFaction);
            _enemyFactionField.value = FactionName(enemyFaction);
            _seedField.value = seed;
            _setupOverlay.RemoveFromClassList("hidden-overlay");
        }

        public void HideSetup()
        {
            _setupOverlay.AddToClassList("hidden-overlay");
        }

        public void HideResult()
        {
            _resultOverlay.AddToClassList("hidden-overlay");
        }

        public void ShowTurnBanner(int playerId, int round)
        {
            var banner = Required<VisualElement>("turn-banner");
            Required<Label>("turn-banner-title").text = playerId == 0 ? "你的回合" : "敌军回合";
            Required<Label>("turn-banner-subtitle").text = "第 " + round + " 回合";
            banner.RemoveFromClassList("hidden-overlay");
            banner.schedule.Execute(() => banner.AddToClassList("hidden-overlay")).ExecuteLater(ReducedMotion ? 40 : 560);
        }

        private void ConfigureStaticInteraction()
        {
            _root.focusable = true;
            _root.RegisterCallback<KeyDownEvent>(OnKeyDown);
            _root.RegisterCallback<PointerMoveEvent>(OnRootPointerMove, TrickleDown.TrickleDown);
            _root.RegisterCallback<PointerUpEvent>(OnRootPointerUp, TrickleDown.TrickleDown);
            _root.RegisterCallback<PointerCaptureOutEvent>(_ => CleanupPointer());

            foreach (var slot in _playerSupportSlots.Concat(_frontlineSlots))
            {
                slot.RegisterCallback<ClickEvent>(evt =>
                {
                    if (TryExecuteTarget(slot))
                    {
                        evt.StopPropagation();
                    }
                });
            }

            _battleSurface.RegisterCallback<ClickEvent>(evt =>
            {
                if (TryExecuteTarget(_battleSurface))
                {
                    evt.StopPropagation();
                }
            });
            _enemyHeadquarters.RegisterCallback<ClickEvent>(evt =>
            {
                if (TryExecuteTarget(_enemyHeadquarters))
                {
                    evt.StopPropagation();
                }
            });

            _endTurnButton.clicked += () =>
            {
                if (!_inputLocked && _engine != null && _engine.State.ActivePlayerId == 0)
                {
                    _executeCommand(new EndTurnCommand(0));
                }
            };
            _commanderButton.clicked += () => SelectSource("commander", SourceKind.Commander, _commanderButton);
            Required<Button>("new-match-button").clicked += () =>
            {
                if (_engine != null)
                {
                    ShowSetup(_engine.State.Players[0].Faction, _engine.State.Players[1].Faction, _engine.State.Seed + 1);
                }
            };
            Required<Button>("rematch-button").clicked += _requestRematch;
        }

        private void ConfigureSetupOverlay()
        {
            var choices = new List<string> { "法兰西", "普鲁士", "俄罗斯" };
            _playerFactionField.choices = choices;
            _enemyFactionField.choices = choices;
            _playerFactionField.value = choices[0];
            _enemyFactionField.value = choices[1];
            Required<Button>("cancel-setup-button").clicked += HideSetup;
            Required<Button>("start-match-button").clicked += () =>
            {
                var player = ParseFactionName(_playerFactionField.value);
                var enemy = ParseFactionName(_enemyFactionField.value);
                if (player == enemy)
                {
                    ShowToast("试玩版请为双方选择不同阵营。");
                    return;
                }

                _startMatch(player, enemy, _seedField.value);
            };
        }

        private void ApplyBattlefieldArt()
        {
            var background = Resources.Load<Texture2D>("Art/battlefield_table");
            if (background != null)
            {
                Required<VisualElement>("battle-backdrop").style.backgroundImage = new StyleBackground(background);
            }
        }

        private void PopulateSlot(VisualElement slot, UnitState unit)
        {
            slot.Clear();
            if (unit == null)
            {
                return;
            }

            var view = CreateUnitView(unit);
            slot.Add(view);
            _unitViews[unit.Id] = view;
        }

        private VisualElement CreateCardView(CardInstance card)
        {
            var definition = card.Definition;
            var view = new VisualElement { name = "card-" + card.InstanceId };
            view.AddToClassList("hand-card");
            view.AddToClassList("faction-" + FactionSlug(definition.Faction));
            if (!GetSourceCommands(card.InstanceId, SourceKind.Card).Any())
            {
                view.AddToClassList("illegal-source");
            }

            var topLine = new VisualElement();
            topLine.AddToClassList("card-topline");
            topLine.Add(Badge(definition.DeployCost.ToString(), "cost-badge"));
            var name = new Label(definition.Name);
            name.AddToClassList("card-name");
            topLine.Add(name);
            topLine.Add(Badge(definition.OperationCost.ToString(), "cost-badge", "operation-badge"));
            view.Add(topLine);

            var art = new VisualElement();
            art.AddToClassList("card-art");
            ApplyCardArt(art, definition.ArtKey);
            view.Add(art);

            var rules = new Label(definition.RulesText);
            rules.AddToClassList("card-rule");
            view.Add(rules);

            var stats = new VisualElement();
            stats.AddToClassList("card-stats");
            if (definition.CardType == CardType.Unit)
            {
                stats.Add(Badge(definition.Attack.ToString(), "stat-badge", "attack-badge"));
                stats.Add(Badge(definition.Health.ToString(), "stat-badge", "health-badge"));
            }
            else
            {
                var eventLabel = new Label("战术命令");
                eventLabel.AddToClassList("micro-copy");
                stats.Add(eventLabel);
            }
            view.Add(stats);

            view.RegisterCallback<PointerDownEvent>(evt => BeginSourcePointer(card.InstanceId, SourceKind.Card, view, evt));
            view.RegisterCallback<ClickEvent>(evt =>
            {
                if (ConsumeSuppressedClick())
                {
                    evt.StopPropagation();
                    return;
                }
                SelectSource(card.InstanceId, SourceKind.Card, view);
                evt.StopPropagation();
            });
            view.RegisterCallback<PointerEnterEvent>(_ => InspectCard(definition));
            return view;
        }

        private VisualElement CreateUnitView(UnitState unit)
        {
            var view = new VisualElement { name = "unit-" + unit.Id };
            view.AddToClassList("unit-view");
            view.AddToClassList("unit-" + FactionSlug(unit.Definition.Faction));
            if (unit.IsExhausted)
            {
                view.AddToClassList("unit-exhausted");
            }
            if (unit.IsShaken)
            {
                view.AddToClassList("unit-shaken");
            }

            var art = new VisualElement();
            art.AddToClassList("unit-art");
            ApplyCardArt(art, unit.Definition.ArtKey);
            var type = new Label(UnitTypeName(unit.Definition.UnitType));
            type.AddToClassList("unit-type");
            art.Add(type);
            view.Add(art);

            var name = new Label(unit.Definition.Name);
            name.AddToClassList("unit-name");
            view.Add(name);

            var footer = new VisualElement();
            footer.AddToClassList("unit-footer");
            var keywords = new Label(string.Join(" · ", unit.Definition.Keywords));
            keywords.AddToClassList("unit-keywords");
            footer.Add(keywords);
            footer.Add(Badge(_engine.GetEffectiveAttack(unit).ToString(), "unit-stat", "attack-badge"));
            footer.Add(Badge(unit.CurrentHealth + "/" + unit.MaxHealth, "unit-stat", "health-badge"));
            view.Add(footer);

            if (unit.OwnerId == 0)
            {
                if (!GetSourceCommands(unit.Id, SourceKind.Unit).Any())
                {
                    view.AddToClassList("illegal-source");
                }
                view.RegisterCallback<PointerDownEvent>(evt => BeginSourcePointer(unit.Id, SourceKind.Unit, view, evt));
            }
            view.RegisterCallback<ClickEvent>(evt =>
            {
                if (ConsumeSuppressedClick())
                {
                    evt.StopPropagation();
                    return;
                }

                if (TryExecuteTarget(view))
                {
                    evt.StopPropagation();
                    return;
                }

                if (unit.OwnerId == 0)
                {
                    SelectSource(unit.Id, SourceKind.Unit, view);
                }
                evt.StopPropagation();
            });
            view.RegisterCallback<PointerEnterEvent>(_ => InspectUnit(unit));
            return view;
        }

        private void BeginSourcePointer(string sourceId, SourceKind kind, VisualElement source, PointerDownEvent evt)
        {
            if (_inputLocked || evt.button != 0 || _engine == null || _engine.State.ActivePlayerId != 0)
            {
                return;
            }

            _pointerId = evt.pointerId;
            _pointerStart = evt.position;
            _pointerSourceElement = source;
            _pointerSourceId = sourceId;
            _pointerSourceKind = kind;

            source.AddToClassList("pressed-source");
            if (_dropTargets.TryGetValue(source, out var pendingCommand) && source != _selectedElement)
            {
                _pendingTargetCommand = pendingCommand;
                SetMagnetTarget(source);
            }
            else if (!SelectSource(sourceId, kind, source))
            {
                source.RemoveFromClassList("pressed-source");
                _pointerId = -1;
                _pointerSourceElement = null;
                _pointerSourceId = null;
                return;
            }

            _root.CapturePointer(evt.pointerId);
            evt.StopPropagation();
        }

        private void OnRootPointerMove(PointerMoveEvent evt)
        {
            if (evt.pointerId != _pointerId || _pointerSourceElement == null)
            {
                return;
            }

            if (_pendingTargetCommand != null)
            {
                evt.StopPropagation();
                return;
            }

            if (!_dragging)
            {
                if (((Vector2)evt.position - _pointerStart).sqrMagnitude < 49f)
                {
                    return;
                }

                _dragging = true;
                _pointerSourceElement.RemoveFromClassList("pressed-source");
                _pointerSourceElement.AddToClassList("dragging-source");
                _dragGhost = new VisualElement();
                _dragGhost.AddToClassList("drag-ghost");
                var title = new Label(GetSourceName(_pointerSourceId, _pointerSourceKind));
                title.AddToClassList("drag-ghost-title");
                _dragGhost.Add(title);
                _dragLayer.Add(_dragGhost);

                if (_dropTargets.Values.Any(command => command is AttackCommand))
                {
                    _attackArrow = new AttackArrowElement();
                    _dragLayer.Insert(0, _attackArrow);
                }
            }

            var local = _dragLayer.WorldToLocal(evt.position);
            _dragGhost.style.left = local.x - 52f;
            _dragGhost.style.top = local.y - 65f;

            var target = FindDropTarget(evt.position, 44f);
            SetMagnetTarget(target);
            if (_attackArrow != null)
            {
                var start = _dragLayer.WorldToLocal(_pointerSourceElement.worldBound.center);
                var end = target == null ? local : _dragLayer.WorldToLocal(target.worldBound.center);
                _attackArrow.SetPoints(start, end);
            }
            evt.StopPropagation();
        }

        private void OnRootPointerUp(PointerUpEvent evt)
        {
            if (evt.pointerId != _pointerId)
            {
                return;
            }

            if (_dragging)
            {
                var target = FindDropTarget(evt.position, 44f);
                _suppressNextClick = true;
                if (target != null && _dropTargets.TryGetValue(target, out var command))
                {
                    target.AddToClassList("drag-accept");
                    ClearSelection();
                    _executeCommand(command);
                }
                else
                {
                    RejectPointerDrop();
                }
            }
            else if (_pendingTargetCommand != null)
            {
                _suppressNextClick = true;
                var command = _pendingTargetCommand;
                ClearSelection();
                _executeCommand(command);
            }
            else if (_pointerSourceElement != null)
            {
                _suppressNextClick = true;
            }

            CleanupPointer();
            evt.StopPropagation();
        }

        private bool SelectSource(string sourceId, SourceKind kind, VisualElement source)
        {
            if (_inputLocked)
            {
                return false;
            }

            var commands = GetSourceCommands(sourceId, kind).ToArray();
            if (commands.Length == 0)
            {
                ShowToast(kind == SourceKind.Card ? "军令不足或没有可用槽位。" : "该单位本回合无法行动。 ");
                return false;
            }

            ClearSelection();
            _selectedSourceId = sourceId;
            _selectedSourceKind = kind;
            _selectedElement = source;
            _selectedElement.AddToClassList("card-selected");

            foreach (var command in commands)
            {
                var target = ResolveTargetElement(command);
                if (target == null)
                {
                    continue;
                }

                if (!_dropTargets.ContainsKey(target))
                {
                    _dropTargets.Add(target, command);
                    target.AddToClassList("legal-target");
                    AddTargetPreview(target, command);
                }
            }

            _turnHint.text = kind == SourceKind.Card
                ? "将卡牌拖到高亮区域，或点击目标。"
                : kind == SourceKind.Commander
                    ? "选择高亮单位作为指挥官能力目标。"
                    : "将单位拖到高亮槽位或目标，或直接点击目标。";
            return _dropTargets.Count > 0;
        }

        private IEnumerable<GameCommand> GetSourceCommands(string sourceId, SourceKind kind)
        {
            foreach (var command in _legalActions)
            {
                if (kind == SourceKind.Card &&
                    ((command is DeployCommand deploy && deploy.CardInstanceId == sourceId) ||
                     (command is PlayEventCommand playEvent && playEvent.CardInstanceId == sourceId)))
                {
                    yield return command;
                }
                else if (kind == SourceKind.Unit &&
                         ((command is MoveCommand move && move.UnitId == sourceId) ||
                          (command is AttackCommand attack && attack.AttackerId == sourceId)))
                {
                    yield return command;
                }
                else if (kind == SourceKind.Commander && command is CommanderCommand)
                {
                    yield return command;
                }
            }
        }

        private VisualElement ResolveTargetElement(GameCommand command)
        {
            if (command is DeployCommand deploy)
            {
                return _playerSupportSlots[deploy.SupportSlot];
            }
            if (command is MoveCommand move)
            {
                return _frontlineSlots[move.FrontlineSlot];
            }
            if (command is AttackCommand attack)
            {
                return attack.TargetKind == TargetKind.Headquarters
                    ? _enemyHeadquarters
                    : FindUnitView(attack.TargetUnitId);
            }
            if (command is PlayEventCommand playEvent)
            {
                return string.IsNullOrEmpty(playEvent.TargetUnitId)
                    ? _battleSurface
                    : FindUnitView(playEvent.TargetUnitId);
            }
            if (command is CommanderCommand commander)
            {
                return FindUnitView(commander.TargetUnitId);
            }
            return null;
        }

        private VisualElement FindUnitView(string unitId)
        {
            return !string.IsNullOrEmpty(unitId) && _unitViews.TryGetValue(unitId, out var view) ? view : null;
        }

        private VisualElement FindDropTarget(Vector2 worldPosition, float magnetRadius = 0f)
        {
            VisualElement nearest = null;
            var nearestDistance = float.MaxValue;
            foreach (var target in _dropTargets.Keys)
            {
                if (target.worldBound.Contains(worldPosition))
                {
                    return target;
                }

                var bounds = target.worldBound;
                var closest = new Vector2(
                    Mathf.Clamp(worldPosition.x, bounds.xMin, bounds.xMax),
                    Mathf.Clamp(worldPosition.y, bounds.yMin, bounds.yMax));
                var distance = (closest - worldPosition).sqrMagnitude;
                if (distance <= magnetRadius * magnetRadius && distance < nearestDistance)
                {
                    nearest = target;
                    nearestDistance = distance;
                }
            }
            return nearest;
        }

        private void AddTargetPreview(VisualElement target, GameCommand command)
        {
            var badge = new Label(CommandPreviewText(command));
            badge.AddToClassList("target-preview-badge");
            target.Add(badge);
            _previewBadges.Add(badge);
        }

        private static string CommandPreviewText(GameCommand command)
        {
            if (command is DeployCommand) return "部署";
            if (command is MoveCommand) return "推进";
            if (command is AttackCommand) return "攻击";
            if (command is CommanderCommand) return "指挥";
            return "执行";
        }

        private void SetMagnetTarget(VisualElement target)
        {
            if (_magnetTarget == target)
            {
                return;
            }
            _magnetTarget?.RemoveFromClassList("magnet-target");
            _magnetTarget = target;
            _magnetTarget?.AddToClassList("magnet-target");
        }

        private void RejectPointerDrop()
        {
            if (_pointerSourceElement != null)
            {
                PulseClass(_pointerSourceElement, "drag-reject", 180);
            }
            ShowToast("这个位置不能执行命令；拖向带动作标签的目标。 ");
        }

        private bool TryExecuteTarget(VisualElement target)
        {
            if (_inputLocked || target == null || !_dropTargets.TryGetValue(target, out var command))
            {
                return false;
            }

            ClearSelection();
            _executeCommand(command);
            return true;
        }

        private void ClearSelection()
        {
            if (_selectedElement != null)
            {
                _selectedElement.RemoveFromClassList("card-selected");
            }
            foreach (var target in _dropTargets.Keys)
            {
                target.RemoveFromClassList("legal-target");
                target.RemoveFromClassList("magnet-target");
            }
            foreach (var badge in _previewBadges)
            {
                badge.RemoveFromHierarchy();
            }
            _previewBadges.Clear();
            _dropTargets.Clear();
            _selectedElement = null;
            _selectedSourceId = null;
            _pendingTargetCommand = null;
            _magnetTarget = null;
            CleanupPointerVisuals();
        }

        private void CleanupPointer()
        {
            if (_pointerId >= 0 && _root.HasPointerCapture(_pointerId))
            {
                _root.ReleasePointer(_pointerId);
            }
            _pointerId = -1;
            _pointerSourceElement?.RemoveFromClassList("pressed-source");
            _pointerSourceElement?.RemoveFromClassList("dragging-source");
            _pointerSourceElement = null;
            _pointerSourceId = null;
            _pendingTargetCommand = null;
            _dragging = false;
            SetMagnetTarget(null);
            CleanupPointerVisuals();
        }

        private void CleanupPointerVisuals()
        {
            _dragGhost?.RemoveFromHierarchy();
            _attackArrow?.RemoveFromHierarchy();
            _dragGhost = null;
            _attackArrow = null;
        }

        private bool ConsumeSuppressedClick()
        {
            if (!_suppressNextClick)
            {
                return false;
            }
            _suppressNextClick = false;
            return true;
        }

        private void InspectCard(CardDefinition definition)
        {
            Required<Label>("inspect-title").text = definition.Name;
            Required<Label>("inspect-type").text = definition.CardType == CardType.Event
                ? FactionName(definition.Faction) + " · 战术命令"
                : FactionName(definition.Faction) + " · " + UnitTypeName(definition.UnitType);
            Required<Label>("inspect-stats").text = definition.CardType == CardType.Event
                ? "部署 " + definition.DeployCost
                : "部署 " + definition.DeployCost + " · 行动 " + definition.OperationCost + " · 攻 " + definition.Attack + " · 血 " + definition.Health;
            Required<Label>("inspect-rules").text = definition.RulesText +
                (definition.Keywords.Count > 0 ? "\n关键词：" + string.Join("、", definition.Keywords) : string.Empty);
            SetInspectArt(definition.Faction, definition.ArtKey);
        }

        private void InspectUnit(UnitState unit)
        {
            InspectCard(unit.Definition);
            Required<Label>("inspect-stats").text =
                "行动 " + unit.Definition.OperationCost + " · 当前攻 " + _engine.GetEffectiveAttack(unit) +
                " · 当前血 " + unit.CurrentHealth + "/" + unit.MaxHealth +
                (unit.IsShaken ? " · 动摇" : string.Empty) +
                (unit.IsExhausted ? " · 已行动" : " · 可行动");
        }

        private void SetInspectArt(Faction faction, string artKey)
        {
            var art = Required<VisualElement>("inspect-art");
            art.RemoveFromClassList("inspect-france");
            art.RemoveFromClassList("inspect-prussia");
            art.RemoveFromClassList("inspect-russia");
            art.AddToClassList("inspect-" + FactionSlug(faction));
            ApplyCardArt(art, artKey);
        }

        private static void ApplyCardArt(VisualElement element, string artKey)
        {
            if (string.IsNullOrEmpty(artKey))
            {
                return;
            }
            var texture = Resources.Load<Texture2D>("Art/Cards/" + artKey);
            if (texture != null)
            {
                element.style.backgroundImage = new StyleBackground(texture);
            }
        }

        private void AnimateBoardReflow(Dictionary<string, Vector2> previousCenters)
        {
            foreach (var pair in previousCenters)
            {
                if (!_unitViews.TryGetValue(pair.Key, out var view) || view.panel == null)
                {
                    continue;
                }

                var delta = pair.Value - view.worldBound.center;
                if (delta.sqrMagnitude < 9f)
                {
                    continue;
                }

                view.AddToClassList("no-transition");
                view.style.translate = new Translate(delta.x, delta.y, 0f);
                view.schedule.Execute(() =>
                {
                    view.RemoveFromClassList("no-transition");
                    view.style.translate = new Translate(0f, 0f, 0f);
                }).ExecuteLater(16);
            }
        }

        private void ShowDestruction(string targetId)
        {
            if (!TryGetTargetCenter(targetId, out var center))
            {
                return;
            }

            var burst = new VisualElement();
            burst.AddToClassList("impact-burst");
            _dragLayer.Add(burst);
            var local = _dragLayer.WorldToLocal(center);
            burst.style.left = local.x - 27f;
            burst.style.top = local.y - 27f;
            burst.schedule.Execute(() => burst.AddToClassList("impact-burst-active")).ExecuteLater(1);
            burst.schedule.Execute(burst.RemoveFromHierarchy).ExecuteLater(280);
        }

        private bool TryGetTargetCenter(string targetId, out Vector2 center)
        {
            if (targetId == "hq-0")
            {
                center = _playerHeadquarters.worldBound.center;
                return true;
            }
            if (targetId == "hq-1")
            {
                center = _enemyHeadquarters.worldBound.center;
                return true;
            }
            if (_unitViews.TryGetValue(targetId, out var view))
            {
                center = view.worldBound.center;
                return true;
            }
            return _lastKnownUnitCenters.TryGetValue(targetId, out center);
        }

        private void ShowAttack(string sourceId, string targetId)
        {
            if (!TryGetTargetCenter(sourceId, out var sourceCenter))
            {
                return;
            }
            if (_unitViews.TryGetValue(sourceId, out var source))
            {
                PulseClass(source, "anim-attack", 150);
            }
            if (!TryGetTargetCenter(targetId, out var targetCenter))
            {
                return;
            }

            var arrow = new AttackArrowElement();
            _dragLayer.Add(arrow);
            arrow.SetPoints(
                _dragLayer.WorldToLocal(sourceCenter),
                _dragLayer.WorldToLocal(targetCenter));
            arrow.schedule.Execute(arrow.RemoveFromHierarchy).ExecuteLater(210);
        }

        private void ShowDamage(string targetId, int amount)
        {
            VisualElement target = null;
            if (targetId == "hq-0")
            {
                target = _playerHeadquarters;
            }
            else if (targetId == "hq-1")
            {
                target = _enemyHeadquarters;
            }
            else
            {
                _unitViews.TryGetValue(targetId, out target);
            }

            if (!TryGetTargetCenter(targetId, out var center))
            {
                return;
            }

            if (target != null)
            {
                PulseClass(target, "anim-hit", 130);
            }
            var popup = new Label(amount <= 0 ? "格挡" : "-" + amount);
            popup.AddToClassList("damage-pop");
            _dragLayer.Add(popup);
            var local = _dragLayer.WorldToLocal(center);
            popup.style.left = local.x - 24f;
            popup.style.top = local.y - 16f;
            popup.schedule.Execute(() => popup.AddToClassList("damage-pop-active")).ExecuteLater(20);
            popup.schedule.Execute(popup.RemoveFromHierarchy).ExecuteLater(390);
        }

        private static void PulseClass(VisualElement element, string className, long durationMilliseconds)
        {
            if (element == null)
            {
                return;
            }
            element.AddToClassList(className);
            element.schedule.Execute(() => element.RemoveFromClassList(className)).ExecuteLater(durationMilliseconds);
        }

        private void ShowResult(GameState state)
        {
            var playerWon = state.WinnerId == 0;
            var draw = state.WinnerId < 0;
            Required<Label>("result-title").text = draw ? "平局" : playerWon ? "胜利" : "战败";
            Required<Label>("result-copy").text = state.EndReason == MatchEndReason.RoundLimit
                ? "达到 30 回合上限，按 HQ 剩余耐久判定。"
                : draw ? "双方总部同时失守。" : playerWon ? "敌方总部已经被攻破。" : "我方总部已经失守。";
            _resultOverlay.RemoveFromClassList("hidden-overlay");
        }

        private void OnKeyDown(KeyDownEvent evt)
        {
            if (evt.keyCode == KeyCode.Escape)
            {
                ClearSelection();
                HideSetup();
                return;
            }

            if ((evt.keyCode == KeyCode.Space || evt.keyCode == KeyCode.E) &&
                !_inputLocked && _engine != null && _engine.State.ActivePlayerId == 0)
            {
                _executeCommand(new EndTurnCommand(0));
                evt.StopPropagation();
            }
            else if (evt.keyCode == KeyCode.D && !_inputLocked)
            {
                var deploy = _legalActions.OfType<DeployCommand>().FirstOrDefault();
                if (deploy != null)
                {
                    _executeCommand(deploy);
                }
                else
                {
                    ShowToast("当前没有可部署单位。 ");
                }
                evt.StopPropagation();
            }
            else if (evt.keyCode == KeyCode.M && !_inputLocked)
            {
                var move = _legalActions.OfType<MoveCommand>().FirstOrDefault();
                if (move != null)
                {
                    _executeCommand(move);
                }
                else
                {
                    ShowToast("当前没有单位可以推进。 ");
                }
                evt.StopPropagation();
            }
            else if (evt.keyCode == KeyCode.A && !_inputLocked)
            {
                var attack = _legalActions.OfType<AttackCommand>().FirstOrDefault();
                if (attack != null)
                {
                    _executeCommand(attack);
                }
                else
                {
                    ShowToast("当前没有合法攻击。 ");
                }
                evt.StopPropagation();
            }
            else if (evt.keyCode == KeyCode.N && _engine != null)
            {
                ShowSetup(_engine.State.Players[0].Faction, _engine.State.Players[1].Faction, _engine.State.Seed + 1);
            }
        }

        private void SetHealthBar(VisualElement fill, int health)
        {
            var percentage = Mathf.Clamp01(health / (float)GameEngine.StartingHeadquartersHealth) * 100f;
            fill.style.width = Length.Percent(percentage);
            fill.EnableInClassList("critical-health", percentage <= 25f);
        }

        private string GetSourceName(string sourceId, SourceKind kind)
        {
            if (kind == SourceKind.Commander)
            {
                return _engine.State.Players[0].CommanderName;
            }
            if (kind == SourceKind.Card)
            {
                return _engine.State.Players[0].Hand.FirstOrDefault(card => card.InstanceId == sourceId)?.Definition.Name ?? "卡牌";
            }
            return _engine.State.FindUnit(sourceId)?.Definition.Name ?? "单位";
        }

        private static VisualElement Badge(string text, params string[] classes)
        {
            var badge = new Label(text);
            foreach (var className in classes)
            {
                badge.AddToClassList(className);
            }
            return badge;
        }

        private T Required<T>(string name) where T : VisualElement
        {
            var element = _root.Q<T>(name);
            if (element == null)
            {
                throw new InvalidOperationException("BattleScreen.uxml 缺少元素：" + name);
            }
            return element;
        }

        private static string FactionSlug(Faction faction)
        {
            switch (faction)
            {
                case Faction.France: return "france";
                case Faction.Prussia: return "prussia";
                default: return "russia";
            }
        }

        private static string FactionName(Faction faction)
        {
            switch (faction)
            {
                case Faction.France: return "法兰西";
                case Faction.Prussia: return "普鲁士";
                default: return "俄罗斯";
            }
        }

        private static Faction ParseFactionName(string name)
        {
            switch (name)
            {
                case "法兰西": return Faction.France;
                case "普鲁士": return Faction.Prussia;
                default: return Faction.Russia;
            }
        }

        private static string UnitTypeName(UnitType unitType)
        {
            switch (unitType)
            {
                case UnitType.Infantry: return "步兵";
                case UnitType.Cavalry: return "骑兵";
                case UnitType.Artillery: return "炮兵";
                case UnitType.Skirmisher: return "散兵";
                default: return "近卫";
            }
        }
    }
}
