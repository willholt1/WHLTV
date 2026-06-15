using WHLTV.Pipeline.Infrastructure.Processes;

namespace WHLTV.Pipeline.Infrastructure.Archives;

public sealed class ArchiveExtractor
{
    private readonly ProcessRunner _processRunner;

    public ArchiveExtractor(ProcessRunner processRunner)
    {
        _processRunner = processRunner;
    }

    public async Task<IReadOnlyList<string>> ExtractRarAsync(
        string archiveFullPath,
        string outputDirectory,
        CancellationToken cancellationToken)
    {
        Directory.CreateDirectory(outputDirectory);

        var result = await _processRunner.RunAsync(
            "7z",
            $"x \"{archiveFullPath}\" -o\"{outputDirectory}\" -y",
            cancellationToken
        );

        var extractedDemos = Directory
            .EnumerateFiles(outputDirectory, "*.dem", SearchOption.AllDirectories)
            .ToList();

        // 7z may return a warning exit code while still extracting usable files.
        if (!result.Success && extractedDemos.Count == 0)
        {
            throw new InvalidOperationException(
                $"Archive extraction failed: {result.StandardError}"
            );
        }

        return extractedDemos;
    }
}