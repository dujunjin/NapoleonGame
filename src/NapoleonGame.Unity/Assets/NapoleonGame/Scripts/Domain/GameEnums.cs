namespace NapoleonGame.Domain
{
    public enum Faction
    {
        France,
        Prussia,
        Russia
    }

    public enum CardType
    {
        Unit,
        Event
    }

    public enum UnitType
    {
        Infantry,
        Cavalry,
        Artillery,
        Skirmisher,
        Guard
    }

    public enum BattleZone
    {
        Support,
        Frontline
    }

    public enum TargetKind
    {
        Unit,
        Headquarters
    }

    public enum MatchEndReason
    {
        None,
        HeadquartersDestroyed,
        RoundLimit,
        Draw
    }

    public enum GameEventType
    {
        MatchStarted,
        TurnStarted,
        CardDrawn,
        CardDeployed,
        EventPlayed,
        UnitMoved,
        AttackStarted,
        Damage,
        UnitShaken,
        UnitRecovered,
        UnitDestroyed,
        CreditsChanged,
        CommanderUsed,
        TurnEnded,
        MatchEnded
    }
}
