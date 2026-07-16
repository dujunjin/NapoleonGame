using System;
using System.Collections.Generic;

namespace NapoleonGame.Domain
{
    public sealed class CommandResult
    {
        private CommandResult(bool succeeded, string reason, IReadOnlyList<GameEvent> events)
        {
            Succeeded = succeeded;
            Reason = reason ?? string.Empty;
            Events = events ?? Array.Empty<GameEvent>();
        }

        public bool Succeeded { get; }
        public string Reason { get; }
        public IReadOnlyList<GameEvent> Events { get; }

        public static CommandResult Success(IReadOnlyList<GameEvent> events)
        {
            return new CommandResult(true, string.Empty, events);
        }

        public static CommandResult Failure(string reason)
        {
            return new CommandResult(false, reason, Array.Empty<GameEvent>());
        }
    }
}
