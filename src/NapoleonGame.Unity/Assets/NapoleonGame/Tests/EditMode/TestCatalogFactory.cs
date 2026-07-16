using System;
using System.Collections.Generic;
using NapoleonGame.Domain;

namespace NapoleonGame.Tests
{
    internal static class TestCatalogFactory
    {
        public static CardCatalog Create(int quantityPerDefinition = 11)
        {
            return new CardCatalog(new[]
            {
                CreateFaction(Faction.France, "法兰西", "napoleon", "拿破仑", "fr", quantityPerDefinition),
                CreateFaction(Faction.Prussia, "普鲁士", "blucher", "布吕歇尔", "pr", quantityPerDefinition),
                CreateFaction(Faction.Russia, "俄罗斯", "kutuzov", "库图佐夫", "ru", quantityPerDefinition)
            });
        }

        public static CardDefinition Unit(
            string id,
            Faction faction,
            UnitType unitType = UnitType.Infantry,
            int deployCost = 1,
            int operationCost = 1,
            int attack = 2,
            int health = 3,
            int quantity = 1,
            params string[] keywords)
        {
            return new CardDefinition(id, id, faction, CardType.Unit, unitType, deployCost,
                operationCost, attack, health, keywords, string.Empty, string.Empty, quantity,
                string.Empty, faction.ToString().ToLowerInvariant() + "_" + unitType.ToString().ToLowerInvariant());
        }

        private static FactionCatalog CreateFaction(
            Faction faction,
            string displayName,
            string commanderId,
            string commanderName,
            string prefix,
            int quantity)
        {
            var cards = new List<CardDefinition>
            {
                Unit(prefix + "-inf", faction, UnitType.Infantry, 1, 1, 2, 3, quantity, "冲锋", "结阵"),
                Unit(prefix + "-cav", faction, UnitType.Cavalry, 2, 2, 3, 3, quantity, "冲锋"),
                Unit(prefix + "-art", faction, UnitType.Artillery, 2, 2, 2, 3, quantity, "远程")
            };
            return new FactionCatalog(faction, displayName, commanderId, commanderName, cards);
        }
    }
}
