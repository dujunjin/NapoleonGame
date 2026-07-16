using System.Collections.Generic;

namespace NapoleonGame.Domain
{
    public sealed class PlayerState
    {
        private readonly List<CardInstance> _deck = new List<CardInstance>();
        private readonly List<CardInstance> _hand = new List<CardInstance>();
        private readonly List<CardInstance> _discard = new List<CardInstance>();

        internal PlayerState(int id, FactionCatalog catalog, bool isHuman)
        {
            Id = id;
            Faction = catalog.Faction;
            Name = catalog.DisplayName;
            CommanderId = catalog.CommanderId;
            CommanderName = catalog.CommanderName;
            IsHuman = isHuman;
            HeadquartersHealth = GameEngine.StartingHeadquartersHealth;
        }

        public int Id { get; }
        public Faction Faction { get; }
        public string Name { get; }
        public string CommanderId { get; }
        public string CommanderName { get; }
        public bool IsHuman { get; }
        public int HeadquartersHealth { get; internal set; }
        public int MaxCredits { get; internal set; }
        public int CurrentCredits { get; internal set; }
        public int FatigueDamage { get; internal set; }
        public int PendingCreditBoost { get; internal set; }
        public bool CommanderUsed { get; internal set; }
        public bool CossackRefundPending { get; internal set; }

        public IReadOnlyList<CardInstance> Deck => _deck;
        public IReadOnlyList<CardInstance> Hand => _hand;
        public IReadOnlyList<CardInstance> Discard => _discard;

        internal List<CardInstance> MutableDeck => _deck;
        internal List<CardInstance> MutableHand => _hand;
        internal List<CardInstance> MutableDiscard => _discard;
    }
}
