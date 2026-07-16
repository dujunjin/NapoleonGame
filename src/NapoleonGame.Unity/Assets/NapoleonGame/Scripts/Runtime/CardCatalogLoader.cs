using System;
using System.Collections.Generic;
using System.Linq;
using NapoleonGame.Domain;
using UnityEngine;

namespace NapoleonGame.Runtime
{
    public static class CardCatalogLoader
    {
        public static CardCatalog Load(TextAsset asset)
        {
            if (asset == null)
            {
                throw new ArgumentNullException(nameof(asset));
            }

            return LoadJson(asset.text);
        }

        public static CardCatalog LoadJson(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
            {
                throw new InvalidOperationException("卡牌目录为空。");
            }

            var dto = JsonUtility.FromJson<CatalogDto>(json);
            if (dto == null || dto.schemaVersion != 1 || dto.factions == null)
            {
                throw new InvalidOperationException("卡牌目录格式无效或版本不受支持。");
            }

            var factions = dto.factions.Select(ConvertFaction).ToArray();
            if (factions.Length != 3)
            {
                throw new InvalidOperationException("试玩版必须包含法兰西、普鲁士、俄罗斯三个阵营。");
            }

            foreach (var faction in factions)
            {
                if (faction.DeckSize != 33)
                {
                    throw new InvalidOperationException(faction.DisplayName + " 牌组必须为 33 张，当前为 " + faction.DeckSize + " 张。");
                }
            }

            return new CardCatalog(factions);
        }

        private static FactionCatalog ConvertFaction(FactionDto dto)
        {
            if (dto == null || dto.cards == null)
            {
                throw new InvalidOperationException("阵营目录缺少卡牌数据。");
            }

            var faction = ParseFaction(dto.id);
            var cards = new List<CardDefinition>();
            foreach (var card in dto.cards)
            {
                if (card == null || card.quantity <= 0)
                {
                    throw new InvalidOperationException(dto.displayName + " 存在数量无效的卡牌。");
                }

                cards.Add(new CardDefinition(
                    card.id,
                    card.name,
                    faction,
                    ParseCardType(card.cardType),
                    ParseUnitType(card.unitType),
                    card.deployCost,
                    card.operationCost,
                    card.attack,
                    card.health,
                    card.keywords ?? Array.Empty<string>(),
                    card.eventEffect,
                    card.subfaction,
                    card.quantity,
                    card.rulesText,
                    card.artKey));
            }

            return new FactionCatalog(faction, dto.displayName, dto.commanderId, dto.commanderName, cards);
        }

        private static Faction ParseFaction(string value)
        {
            switch (value)
            {
                case "france": return Faction.France;
                case "prussia": return Faction.Prussia;
                case "russia": return Faction.Russia;
                default: throw new InvalidOperationException("未知阵营：" + value);
            }
        }

        private static CardType ParseCardType(string value)
        {
            switch (value)
            {
                case "unit": return CardType.Unit;
                case "event": return CardType.Event;
                default: throw new InvalidOperationException("未知卡牌类型：" + value);
            }
        }

        private static UnitType ParseUnitType(string value)
        {
            switch (value)
            {
                case "infantry": return UnitType.Infantry;
                case "cavalry": return UnitType.Cavalry;
                case "artillery": return UnitType.Artillery;
                case "skirmisher": return UnitType.Skirmisher;
                case "guard": return UnitType.Guard;
                default: throw new InvalidOperationException("未知单位类型：" + value);
            }
        }

        [Serializable]
        private sealed class CatalogDto
        {
            public int schemaVersion;
            public FactionDto[] factions;
        }

        [Serializable]
        private sealed class FactionDto
        {
            public string id;
            public string displayName;
            public string commanderId;
            public string commanderName;
            public CardDto[] cards;
        }

        [Serializable]
        private sealed class CardDto
        {
            public string id;
            public string name;
            public string cardType;
            public string unitType;
            public int deployCost;
            public int operationCost;
            public int attack;
            public int health;
            public string[] keywords;
            public string eventEffect;
            public string subfaction;
            public int quantity;
            public string rulesText;
            public string artKey;
        }
    }
}
