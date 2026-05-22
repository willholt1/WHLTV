namespace WHLTV.Pipeline.Domain.Enums
{
    public enum DemoFileStatus
    {
        ReadyToConvert,
        Converting,
        ReadyToValidate,
        Validating,
        ReadyToStore,
        Storing,
        Stored,
        Failed
    }
}
