namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ValidateWorker : BackgroundService
{
    private readonly ILogger<ValidateWorker> _logger;

    public ValidateWorker(ILogger<ValidateWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Validate worker is currently a placeholder and is not configured to process jobs.");

        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
        }
    }
}