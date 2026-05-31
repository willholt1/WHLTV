namespace WHLTV.Pipeline.Infrastructure.Docker;

public sealed class DockerRunOptions
{
    public required string ImageName { get; init; }

    public string? ContainerName { get; init; }

    public bool RemoveWhenFinished { get; init; } = true;

    public Dictionary<string, string> VolumeMounts { get; init; } = new();

    public Dictionary<string, string> EnvironmentVariables { get; init; } = new();

    public List<string> Arguments { get; init; } = new();

    public string? WorkingDirectory { get; init; }
}