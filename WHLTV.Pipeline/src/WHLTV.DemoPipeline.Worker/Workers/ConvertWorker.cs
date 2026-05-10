protected override async Task ExecuteAsync(CancellationToken stoppingToken)
{
    while (!stoppingToken.IsCancellationRequested)
    {
        var job = await _repository.TryClaimNextJob();

        if (job is null)
        {
            await Task.Delay(TimeSpan.FromSeconds(30), stoppingToken);
            continue;
        }

        try
        {
            await ProcessJob(job, stoppingToken);
            await _repository.MarkNextStatus(job.Id);
        }
        catch (Exception ex)
        {
            await _repository.MarkFailed(job.Id, ex.Message);
        }
    }
}