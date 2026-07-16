using System;
using System.Collections.Generic;
using System.Linq;

namespace NapoleonGame.Domain
{
    public sealed class FactionCatalog
    {
        public FactionCatalog(Faction faction, string displayName, string commanderId, string commanderName, IEnumerable<CardDefinition> cards)
        {
            Faction = faction;
            DisplayName = displayName;
            CommanderId = commanderId;
            CommanderName = commanderName;
            Cards = new List<CardDefinition>(cards ?? throw new ArgumentNullException(nameof(cards)));
        }

        public Faction Faction { get; }
        public string DisplayName { get; }
        public string CommanderId { get; }
        public string CommanderName { get; }
        public IReadOnlyList<CardDefinition> Cards { get; }

        public int DeckSize => Cards.Sum(card => card.Quantity);
    }

    public sealed class CardCatalog
    {
        private readonly Dictionary<Faction, FactionCatalog> _factions;

        public CardCatalog(IEnumerable<FactionCatalog> factions)
        {
            _factions = (factions ?? throw new ArgumentNullException(nameof(factions)))
                .ToDictionary(faction => faction.Faction);
        }

        public IReadOnlyCollection<FactionCatalog> Factions => _factions.Values;

        public FactionCatalog GetFaction(Faction faction)
        {
            if (!_factions.TryGetValue(faction, out var catalog))
            {
                throw new InvalidOperationException("Missing catalog for " + faction + ".");
            }

            return catalog;
        }
    }
}
