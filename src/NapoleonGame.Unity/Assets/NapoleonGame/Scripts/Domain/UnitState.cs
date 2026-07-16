using System.Collections.Generic;

namespace NapoleonGame.Domain
{
    public sealed class UnitState
    {
        private readonly HashSet<string> _extraKeywords = new HashSet<string>();

        internal UnitState(string id, int ownerId, CardDefinition definition, BattleZone zone, int slot)
        {
            Id = id;
            OwnerId = ownerId;
            Definition = definition;
            Zone = zone;
            Slot = slot;
            CurrentHealth = definition.Health;
        }

        public string Id { get; }
        public int OwnerId { get; }
        public CardDefinition Definition { get; }
        public BattleZone Zone { get; internal set; }
        public int Slot { get; internal set; }
        public int CurrentHealth { get; internal set; }
        public int AttackModifier { get; internal set; }
        public int HealthModifier { get; internal set; }
        public bool IsExhausted { get; internal set; }
        public bool DeployedThisTurn { get; internal set; }
        public bool HasUsedEvade { get; internal set; }
        public bool HasUsedVolley { get; internal set; }
        public bool IsShaken { get; internal set; }
        public bool ShakenAtTurnStart { get; internal set; }
        public bool OnWoundedExhausted { get; internal set; }

        public int MaxHealth => Definition.Health + HealthModifier;
        public bool IsDead => CurrentHealth <= 0;

        public bool HasKeyword(string keyword)
        {
            return Definition.HasKeyword(keyword) || _extraKeywords.Contains(keyword);
        }

        internal void AddKeyword(string keyword)
        {
            _extraKeywords.Add(keyword);
        }
    }
}
