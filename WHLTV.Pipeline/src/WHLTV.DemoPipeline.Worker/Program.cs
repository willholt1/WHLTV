using WHLTV.DemoPipeline.Worker.Workers;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
using WHLTV.Pipeline.Infrastructure.Docker;
using WHLTV.Pipeline.Infrastructure.Archives;
using WHLTV.Pipeline.Infrastructure.Storage;
using DotNetEnv;

Env.Load();

var dbhost = Environment.GetEnvironmentVariable("DB_HOST");
var dbport = Environment.GetEnvironmentVariable("DB_PORT");
var db = Environment.GetEnvironmentVariable("DB_NAME");
var dbuser = Environment.GetEnvironmentVariable("DB_USER");
var dbpass = Environment.GetEnvironmentVariable("DB_PASSWORD");


var builder = Host.CreateApplicationBuilder(args);

var connectionString =
    $"Host={dbhost};Port={dbport};Database={db};Username={dbuser};Password={dbpass}";

builder.Services.AddSingleton(new DbConnectionFactory(connectionString));
builder.Services.AddSingleton<DemoDownloadJobRepository>();
builder.Services.AddSingleton<DemoPipelineLogsRepository>();

builder.Services.AddSingleton<ProcessRunner>();
builder.Services.AddSingleton<ArchiveExtractor>();

builder.Services.Configure<StorageOptions>(
    builder.Configuration.GetSection("Storage")
);
builder.Services.AddSingleton<PathResolver>();

builder.Services.AddHostedService<ExtractWorker>();
// builder.Services.AddHostedService<ConvertWorker>();
// builder.Services.AddHostedService<ValidateWorker>();
// builder.Services.AddHostedService<StoreWorker>();
// builder.Services.AddHostedService<CleanupWorker>();

var host = builder.Build();

host.Run();

