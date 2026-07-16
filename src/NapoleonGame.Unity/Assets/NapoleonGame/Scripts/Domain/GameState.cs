using System.Collections.Generic;

namespace NapoleonGame.Domain
{
    public sealed class GameState
    {
        private readonly UnitState[,] _support = new UnitState[2, GameEngine.SupportCapacity];
        private readonly UnitState[] _frontline = new UnitState[GameEngine.FrontlineCapacity];

        internal GameState(PlayerState playerOne, PlayerState playerTwo, int seed)
        {
            Players = new[] { playerOne, playerTwo };
            Seed = seed;
            Round = 1;
            ActivePlayerId = 0;
            WinnerId = -2;
        }

        public PlayerState[] Players { get; }
        public int Seed { get; }
        public int Round { get; internal set; }
        public int ActivePlayerId { get; internal set; }
        public bool IsEnded { get; internal set; }
        public int WinnerId { get; internal set; }
        public MatchEndReason EndReason { get; internal set; }
        public long EventSequence { get; internal set; }

        public int FrontlineOwner
        {
            get
            {
                for (var index = 0; index < _frontline.Length; index++)
                {
                    if (_frontline[index] != null)
                    {
                        return _frontline[index].OwnerId;
                    }
                }

                return -1;
            }
        }

        public UnitState GetSupportUnit(int playerId, int slot)
        {
            return IsSupportSlot(slot) ? _support[playerId, slot] : null;
        }

        public UnitState GetFrontlineUnit(int slot)
        {
            return IsFrontlineSlot(slot) ? _frontline[slot] : null;
        }

        public IEnumerable<UnitState> GetSupportUnits(int playerId)
        {
            for (var slot = 0; slot < GameEngine.SupportCapacity; slot++)
            {
                var unit = _support[playerId, slot];
                if (unit != null)
                {
                    yield return unit;
                }
            }
        }

        public IEnumerable<UnitState> GetFrontlineUnits()
        {
            for (var slot = 0; slot < GameEngine.FrontlineCapacity; slot++)
            {
                var unit = _frontline[slot];
                if (unit != null)
                {
                    yield return unit;
                }
            }
        }

        public IEnumerable<UnitState> GetUnits(int playerId)
        {
            foreach (var unit in GetSupportUnits(playerId))
            {
                yield return unit;
            }

            foreach (var unit in GetFrontlineUnits())
            {
                if (unit.OwnerId == playerId)
                {
                    yield return unit;
                }
            }
        }

        public UnitState FindUnit(string unitId)
        {
            if (string.IsNullOrEmpty(unitId))
            {
                return null;
            }

            for (var player = 0; player < 2; player++)
            {
                for (var slot = 0; slot < GameEngine.SupportCapacity; slot++)
                {
                    var unit = _support[player, slot];
                    if (unit != null && unit.Id == unitId)
                    {
                        return unit;
                    }
                }
            }

            for (var slot = 0; slot < GameEngine.FrontlineCapacity; slot++)
            {
                var unit = _frontline[slot];
                if (unit != null && unit.Id == unitId)
                {
                    return unit;
                }
            }

            return null;
        }

        internal void SetSupportUnit(int playerId, int slot, UnitState unit)
        {
            _support[playerId, slot] = unit;
        }

        internal void SetFrontlineUnit(int slot, UnitState unit)
        {
            _frontline[slot] = unit;
        }

        internal static bool IsSupportSlot(int slot)
        {
            return slot >= 0 && slot < GameEngine.SupportCapacity;
        }

        internal static bool IsFrontlineSlot(int slot)
        {
            return slot >= 0 && slot < GameEngine.FrontlineCapacity;
        }
    }
}
