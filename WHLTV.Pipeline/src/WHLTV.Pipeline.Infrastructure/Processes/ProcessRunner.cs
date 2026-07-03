using System.Diagnostics;

namespace WHLTV.Pipeline.Infrastructure.Processes;

public sealed class ProcessRunner
{
    public async Task<ProcessResult> RunAsync(
        string fileName,
        string arguments,
        CancellationToken cancellationToken)
    {
        using var process = new Process();

        process.StartInfo = new ProcessStartInfo
        {
            FileName = fileName,
            Arguments = arguments,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };

        process.Start();

        // Read both pipes concurrently to prevent deadlock: if only one pipe is
        // drained at a time and the other fills its OS buffer (~64 KB), the child
        // process blocks on pipe_write at 0% CPU until the reader catches up.
        var stdoutTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
        var stderrTask = process.StandardError.ReadToEndAsync(cancellationToken);

        await Task.WhenAll(stdoutTask, stderrTask);
        await process.WaitForExitAsync(cancellationToken);

        return new ProcessResult(
            process.ExitCode,
            stdoutTask.Result,
            stderrTask.Result
        );
    }
}