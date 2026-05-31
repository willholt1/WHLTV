using System.Text;
using Microsoft.Extensions.Logging;
using WHLTV.Pipeline.Infrastructure.Processes;

namespace WHLTV.Pipeline.Infrastructure.Docker;

public sealed class DockerRunner
{
    private readonly ProcessRunner _processRunner;
    private readonly ILogger<DockerRunner> _logger;

    public DockerRunner(
        ProcessRunner processRunner,
        ILogger<DockerRunner> logger)
    {
        _processRunner = processRunner;
        _logger = logger;
    }

    public async Task<ProcessResult> RunAsync(
        DockerRunOptions options,
        CancellationToken cancellationToken)
    {
        string arguments = BuildDockerRunArguments(options);

        _logger.LogInformation(
            "Running Docker image {ImageName}",
            options.ImageName
        );

        return await _processRunner.RunAsync(
            "docker",
            arguments,
            cancellationToken
        );
    }

    private static string BuildDockerRunArguments(DockerRunOptions options)
    {
        var args = new StringBuilder();

        args.Append("run ");

        if (options.RemoveWhenFinished)
        {
            args.Append("--rm ");
        }

        if (!string.IsNullOrWhiteSpace(options.ContainerName))
        {
            args.Append("--name ");
            args.Append(Quote(options.ContainerName));
            args.Append(' ');
        }

        if (!string.IsNullOrWhiteSpace(options.WorkingDirectory))
        {
            args.Append("-w ");
            args.Append(Quote(options.WorkingDirectory));
            args.Append(' ');
        }

        foreach (var volume in options.VolumeMounts)
        {
            args.Append("-v ");
            args.Append(Quote($"{volume.Key}:{volume.Value}"));
            args.Append(' ');
        }

        foreach (var env in options.EnvironmentVariables)
        {
            args.Append("-e ");
            args.Append(Quote($"{env.Key}={env.Value}"));
            args.Append(' ');
        }

        args.Append(Quote(options.ImageName));

        foreach (var argument in options.Arguments)
        {
            args.Append(' ');
            args.Append(Quote(argument));
        }

        return args.ToString();
    }

    private static string Quote(string value)
    {
        return $"\"{value.Replace("\"", "\\\"")}\"";
    }
}