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
        if (Directory.Exists(outputDirectory))
        {
            Directory.Delete(outputDirectory, recursive: true);
        }
        Directory.CreateDirectory(outputDirectory);

        var ext = Path.GetExtension(archiveFullPath);
        string fileName;
        string arguments;

        if (ext.Equals(".rar", StringComparison.OrdinalIgnoreCase))
        {
            fileName = "unrar";
            // unrar x -y <archive> <destination/> — trailing slash required
            arguments = $"x -y \"{archiveFullPath}\" \"{outputDirectory}/\"";
        }
        else
        {
            fileName = "7z";
            arguments = $"x \"{archiveFullPath}\" -o\"{outputDirectory}\" -y";
        }

        var result = await _processRunner.RunAsync(fileName, arguments, cancellationToken);

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