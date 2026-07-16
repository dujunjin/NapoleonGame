using System;
using System.Collections.Generic;

namespace NapoleonGame.Domain
{
    public sealed class CardDefinition
    {
        private readonly HashSet<string> _keywords;

        public CardDefinition(
            string id,
            string name,
            Faction faction,
            CardType cardType,
            UnitType unitType,
            int deployCost,
            int operationCost,
            int attack,
            int health,
            IEnumerable<string> keywords,
            string eventEffect,
            string subfaction,
            int quantity,
            string rulesText,
            string artKey)
        {
            Id = id ?? throw new ArgumentNullException(nameof(id));
            Name = name ?? throw new ArgumentNullException(nameof(name));
            Faction = faction;
            CardType = cardType;
            UnitType = unitType;
            DeployCost = deployCost;
            OperationCost = operationCost;
            Attack = attack;
            Health = health;
            _keywords = new HashSet<string>(keywords ?? Array.Empty<string>());
            EventEffect = eventEffect ?? string.Empty;
            Subfaction = subfaction ?? string.Empty;
            Quantity = quantity;
            RulesText = rulesText ?? string.Empty;
            ArtKey = artKey ?? string.Empty;
        }

        public string Id { get; }
        public string Name { get; }
        public Faction Faction { get; }
        public CardType CardType { get; }
        public UnitType UnitType { get; }
        public int DeployCost { get; }
        public int OperationCost { get; }
        public int Attack { get; }
        public int Health { get; }
        public IReadOnlyCollection<string> Keywords => _keywords;
        public string EventEffect { get; }
        public string Subfaction { get; }
        public int Quantity { get; }
        public string RulesText { get; }
        public string ArtKey { get; }

        public bool HasKeyword(string keyword)
        {
            return _keywords.Contains(keyword);
        }
    }
}
