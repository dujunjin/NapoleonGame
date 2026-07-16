namespace NapoleonGame.Domain
{
    public sealed class CardInstance
    {
        public CardInstance(string instanceId, CardDefinition definition)
        {
            InstanceId = instanceId;
            Definition = definition;
        }

        public string InstanceId { get; }
        public CardDefinition Definition { get; }
    }
}
