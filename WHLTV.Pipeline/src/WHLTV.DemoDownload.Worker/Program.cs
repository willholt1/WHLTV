using WHLTV.DemoDownload.Worker.Workers;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;
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
builder.Services.AddHostedService<DownloadWorker>();

var host = builder.Build();

host.Run();

