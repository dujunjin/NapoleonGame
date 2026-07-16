namespace NapoleonGame.Domain
{
    public sealed class GameEvent
    {
        public GameEvent(long sequence, GameEventType type, int playerId, string sourceId, string targetId, int amount, string message)
        {
            Sequence = sequence;
            Type = type;
            PlayerId = playerId;
            SourceId = sourceId ?? string.Empty;
            TargetId = targetId ?? string.Empty;
            Amount = amount;
            Message = message ?? string.Empty;
        }

        public long Sequence { get; }
        public GameEventType Type { get; }
        public int PlayerId { get; }
        public string SourceId { get; }
        public string TargetId { get; }
        public int Amount { get; }
        public string Message { get; }
    }
}
