namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class StoreWorker : BackgroundService
{
    private readonly ILogger<StoreWorker> _logger;

    public StoreWorker(ILogger<StoreWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Store worker is currently a placeholder and is not configured to process jobs.");

        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
        }
    }
}