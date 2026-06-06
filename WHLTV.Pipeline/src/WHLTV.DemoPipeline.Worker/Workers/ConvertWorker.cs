namespace WHLTV.DemoPipeline.Worker.Workers;

public sealed class ConvertWorker : BackgroundService
{
    private readonly ILogger<ConvertWorker> _logger;

    public ConvertWorker(ILogger<ConvertWorker> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Convert worker is currently a placeholder and is not configured to process jobs.");

        while (!stoppingToken.IsCancellationRequested)
        {
            await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
        }
    }
}