using System.Linq;
using NUnit.Framework;
using NapoleonGame.Domain;
using NapoleonGame.Runtime;
using UnityEditor;
using UnityEngine;

namespace NapoleonGame.Tests
{
    public sealed class GameEngineTests
    {
        [Test]
        public void StartMatchBuildsAsymmetricOpeningHandsAndFirstCredit()
        {
            var engine = NewEngine(42);

            Assert.That(engine.State.Players[0].Hand.Count, Is.EqualTo(4));
            Assert.That(engine.State.Players[1].Hand.Count, Is.EqualTo(5));
            Assert.That(engine.State.Players[0].CurrentCredits, Is.EqualTo(1));
            Assert.That(engine.State.ActivePlayerId, Is.EqualTo(0));
        }

        [Test]
        public void SameSeedProducesSameOpeningDefinitions()
        {
            var first = NewEngine(1977);
            var second = NewEngine(1977);

            CollectionAssert.AreEqual(
                first.State.Players[0].Hand.Select(card => card.Definition.Id).ToArray(),
                second.State.Players[0].Hand.Select(card => card.Definition.Id).ToArray());
            CollectionAssert.AreEqual(
                first.State.Players[1].Hand.Select(card => card.Definition.Id).ToArray(),
                second.State.Players[1].Hand.Select(card => card.Definition.Id).ToArray());
        }

        [Test]
        public void ExportedUnityCatalogLoadsThreeCompleteFactionDecks()
        {
            var asset = AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/NapoleonGame/Data/card_catalog.json");

            var catalog = CardCatalogLoader.Load(asset);

            Assert.That(catalog.Factions.Count, Is.EqualTo(3));
            Assert.That(catalog.Factions.All(faction => faction.DeckSize == 33), Is.True);
            Assert.That(catalog.Factions.Sum(faction => faction.DeckSize), Is.EqualTo(99));
        }

        [Test]
        public void EmbeddedUiFontContainsSimplifiedChineseGlyphs()
        {
            var font = AssetDatabase.LoadAssetAtPath<Font>("Assets/NapoleonGame/Fonts/NotoSansCJKsc-Regular.otf");

            Assert.That(font, Is.Not.Null);
            Assert.That(font.HasCharacter('法'), Is.True);
            Assert.That(font.HasCharacter('兰'), Is.True);
            Assert.That(font.HasCharacter('西'), Is.True);
        }

        [Test]
        public void DeploySpendsCreditsAndOccupiesSupportSlot()
        {
            var engine = NewEngine(2);
            var deploy = engine.GetLegalActions(0).OfType<DeployCommand>().First();

            var before = engine.State.Players[0].CurrentCredits;
            var result = engine.Execute(deploy);

            Assert.That(result.Succeeded, Is.True, result.Reason);
            Assert.That(engine.State.GetSupportUnit(0, deploy.SupportSlot), Is.Not.Null);
            Assert.That(engine.State.Players[0].CurrentCredits, Is.LessThan(before));
        }

        [Test]
        public void EnemyCannotEnterAnOccupiedFrontline()
        {
            var engine = NewEngine(4);
            var unit = new UnitState("friendly-ready", 0,
                TestCatalogFactory.Unit("friendly", Faction.France, keywords: new[] { "冲锋" }),
                BattleZone.Support, 0);
            engine.State.SetSupportUnit(0, 0, unit);
            engine.State.Players[0].CurrentCredits = 10;
            Assert.That(engine.Execute(new MoveCommand(0, unit.Id, 2)).Succeeded, Is.True);
            Assert.That(engine.Execute(new EndTurnCommand(0)).Succeeded, Is.True);

            var enemy = new UnitState("enemy-ready", 1,
                TestCatalogFactory.Unit("enemy", Faction.Prussia, keywords: new[] { "冲锋" }),
                BattleZone.Support, 0);
            engine.State.SetSupportUnit(1, 0, enemy);
            engine.State.Players[1].CurrentCredits = 10;

            Assert.That(engine.GetLegalActions(1).OfType<MoveCommand>(), Is.Empty);
        }

        [Test]
        public void FrontlineUnitCanAttackHeadquartersAfterReady()
        {
            var engine = NewEngine(8);
            var attacker = TestCatalogFactory.Unit("attacker", Faction.France, attack: 4, health: 4, keywords: new[] { "冲锋" });
            var unit = new UnitState("front-attacker", 0, attacker, BattleZone.Frontline, 1);
            engine.State.SetFrontlineUnit(1, unit);
            engine.State.Players[0].CurrentCredits = 5;

            var hqAttack = engine.GetLegalActions(0).OfType<AttackCommand>()
                .Single(action => action.TargetKind == TargetKind.Headquarters);
            var result = engine.Execute(hqAttack);

            Assert.That(result.Succeeded, Is.True, result.Reason);
            Assert.That(engine.State.Players[1].HeadquartersHealth, Is.EqualTo(GameEngine.StartingHeadquartersHealth - 4));
        }

        [Test]
        public void GuardRestrictsUnitAttackTargets()
        {
            var engine = NewEngine(9);
            var attacker = new UnitState("attacker", 0,
                TestCatalogFactory.Unit("a", Faction.France, attack: 3, health: 4), BattleZone.Frontline, 1);
            var guard = new UnitState("guard", 1,
                TestCatalogFactory.Unit("g", Faction.Prussia, health: 5, keywords: new[] { "守卫" }), BattleZone.Support, 0);
            var other = new UnitState("other", 1,
                TestCatalogFactory.Unit("o", Faction.Prussia), BattleZone.Support, 1);
            engine.State.SetFrontlineUnit(1, attacker);
            engine.State.SetSupportUnit(1, 0, guard);
            engine.State.SetSupportUnit(1, 1, other);
            engine.State.Players[0].CurrentCredits = 5;

            var targets = engine.GetLegalActions(0).OfType<AttackCommand>()
                .Where(action => action.TargetKind == TargetKind.Unit)
                .Select(action => action.TargetUnitId)
                .Distinct()
                .ToArray();

            CollectionAssert.AreEqual(new[] { guard.Id }, targets);
        }

        [Test]
        public void HeavyDamageMarksSurvivingUnitShaken()
        {
            var engine = NewEngine(11);
            var attacker = new UnitState("attacker", 0,
                TestCatalogFactory.Unit("a", Faction.France, attack: 2, health: 6), BattleZone.Frontline, 2);
            var defender = new UnitState("defender", 1,
                TestCatalogFactory.Unit("d", Faction.Prussia, attack: 1, health: 3), BattleZone.Support, 0);
            engine.State.SetFrontlineUnit(2, attacker);
            engine.State.SetSupportUnit(1, 0, defender);
            engine.State.Players[0].CurrentCredits = 5;

            var result = engine.Execute(new AttackCommand(0, attacker.Id, TargetKind.Unit, defender.Id));

            Assert.That(result.Succeeded, Is.True, result.Reason);
            Assert.That(defender.CurrentHealth, Is.EqualTo(1));
            Assert.That(defender.IsShaken, Is.True);
        }

        [Test]
        public void EmptyDeckAppliesEscalatingFatigue()
        {
            var catalog = TestCatalogFactory.Create(0);
            var engine = new GameEngine(catalog);
            engine.StartMatch(Faction.France, Faction.Prussia, 3);

            Assert.That(engine.State.Players[0].FatigueDamage, Is.EqualTo(4));
            Assert.That(engine.State.Players[0].HeadquartersHealth, Is.EqualTo(10));
            Assert.That(engine.State.Players[1].FatigueDamage, Is.EqualTo(5));
            Assert.That(engine.State.Players[1].HeadquartersHealth, Is.EqualTo(5));
        }

        [Test]
        public void SeededAiMatchAlwaysTerminates()
        {
            var engine = NewEngine(21);
            var ai = new AiAgent();

            var actions = ai.RunToCompletion(engine);

            Assert.That(actions, Is.GreaterThan(0));
            Assert.That(engine.State.IsEnded, Is.True);
            Assert.That(engine.State.Round, Is.LessThanOrEqualTo(GameEngine.RoundLimit + 1));
        }

        private static GameEngine NewEngine(int seed)
        {
            var engine = new GameEngine(TestCatalogFactory.Create());
            var result = engine.StartMatch(Faction.France, Faction.Prussia, seed);
            Assert.That(result.Succeeded, Is.True, result.Reason);
            return engine;
        }
    }
}
