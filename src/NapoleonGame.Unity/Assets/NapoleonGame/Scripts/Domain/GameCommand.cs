namespace NapoleonGame.Domain
{
    public abstract class GameCommand
    {
        protected GameCommand(int playerId)
        {
            PlayerId = playerId;
        }

        public int PlayerId { get; }
    }

    public sealed class DeployCommand : GameCommand
    {
        public DeployCommand(int playerId, string cardInstanceId, int supportSlot) : base(playerId)
        {
            CardInstanceId = cardInstanceId;
            SupportSlot = supportSlot;
        }

        public string CardInstanceId { get; }
        public int SupportSlot { get; }
    }

    public sealed class MoveCommand : GameCommand
    {
        public MoveCommand(int playerId, string unitId, int frontlineSlot) : base(playerId)
        {
            UnitId = unitId;
            FrontlineSlot = frontlineSlot;
        }

        public string UnitId { get; }
        public int FrontlineSlot { get; }
    }

    public sealed class AttackCommand : GameCommand
    {
        public AttackCommand(int playerId, string attackerId, TargetKind targetKind, string targetUnitId = null) : base(playerId)
        {
            AttackerId = attackerId;
            TargetKind = targetKind;
            TargetUnitId = targetUnitId;
        }

        public string AttackerId { get; }
        public TargetKind TargetKind { get; }
        public string TargetUnitId { get; }
    }

    public sealed class PlayEventCommand : GameCommand
    {
        public PlayEventCommand(int playerId, string cardInstanceId, string targetUnitId = null) : base(playerId)
        {
            CardInstanceId = cardInstanceId;
            TargetUnitId = targetUnitId;
        }

        public string CardInstanceId { get; }
        public string TargetUnitId { get; }
    }

    public sealed class CommanderCommand : GameCommand
    {
        public CommanderCommand(int playerId, string targetUnitId) : base(playerId)
        {
            TargetUnitId = targetUnitId;
        }

        public string TargetUnitId { get; }
    }

    public sealed class EndTurnCommand : GameCommand
    {
        public EndTurnCommand(int playerId) : base(playerId)
        {
        }
    }
}
