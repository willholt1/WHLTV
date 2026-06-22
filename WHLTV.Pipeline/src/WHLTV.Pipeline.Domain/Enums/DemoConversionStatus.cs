namespace WHLTV.Pipeline.Domain.Enums
{
    public enum DemoConversionStatus
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
