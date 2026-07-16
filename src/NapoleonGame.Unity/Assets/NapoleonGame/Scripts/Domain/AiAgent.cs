using System;
using System.Collections.Generic;
using System.Linq;

namespace NapoleonGame.Domain
{
    public sealed class AiAgent
    {
        public GameCommand Choose(GameEngine engine, int playerId)
        {
            var legal = engine.GetLegalActions(playerId);
            if (legal.Count == 0)
            {
                return new EndTurnCommand(playerId);
            }

            return legal
                .Select((command, index) => new ScoredCommand(command, Score(engine, command), index))
                .OrderByDescending(item => item.Score)
                .ThenBy(item => item.Index)
                .First()
                .Command;
        }

        public int RunToCompletion(GameEngine engine, int safetyLimit = 3000)
        {
            var actions = 0;
            while (!engine.State.IsEnded && actions < safetyLimit)
            {
                var command = Choose(engine, engine.State.ActivePlayerId);
                var result = engine.Execute(command);
                if (!result.Succeeded)
                {
                    throw new InvalidOperationException("AI produced illegal command: " + result.Reason);
                }
                actions += 1;
            }

            if (!engine.State.IsEnded)
            {
                throw new InvalidOperationException("AI match exceeded safety limit.");
            }

            return actions;
        }

        private static int Score(GameEngine engine, GameCommand command)
        {
            if (command is AttackCommand attack)
            {
                var attacker = engine.State.FindUnit(attack.AttackerId);
                var damage = attacker == null ? 0 : engine.GetEffectiveAttack(attacker);
                if (attack.TargetKind == TargetKind.Headquarters)
                {
                    var enemy = engine.State.Players[1 - command.PlayerId];
                    return damage >= enemy.HeadquartersHealth ? 10000 : 700 + damage * 10;
                }

                var target = engine.State.FindUnit(attack.TargetUnitId);
                var lethal = target != null && damage >= target.CurrentHealth;
                return lethal ? 600 + target.Definition.DeployCost * 10 : 300 + damage - (target?.CurrentHealth ?? 0);
            }

            if (command is PlayEventCommand)
            {
                return 260;
            }

            if (command is CommanderCommand)
            {
                return 240;
            }

            if (command is DeployCommand deploy)
            {
                var card = engine.State.Players[command.PlayerId].Hand.First(item => item.InstanceId == deploy.CardInstanceId);
                return 180 + card.Definition.Attack + card.Definition.Health - card.Definition.DeployCost;
            }

            if (command is MoveCommand move)
            {
                var unit = engine.State.FindUnit(move.UnitId);
                return 120 + (unit == null ? 0 : engine.GetEffectiveAttack(unit));
            }

            return command is EndTurnCommand ? -1000 : 0;
        }

        private sealed class ScoredCommand
        {
            public ScoredCommand(GameCommand command, int score, int index)
            {
                Command = command;
                Score = score;
                Index = index;
            }

            public GameCommand Command { get; }
            public int Score { get; }
            public int Index { get; }
        }
    }
}
