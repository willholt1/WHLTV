using WHLTV.DemoPipeline.Worker.Workers;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.DataAccess.Repositories;
using WHLTV.Pipeline.Infrastructure.Processes;

var builder = Host.CreateApplicationBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("WHLTV")
    ?? throw new InvalidOperationException("Missing WHLTV connection string.");

builder.Services.AddSingleton(new DbConnectionFactory(connectionString));

builder.Services.AddSingleton<DemoDownloadJobRepository>();
builder.Services.AddSingleton<DemoFileJobRepository>();
builder.Services.AddSingleton<ProcessRunner>();

builder.Services.AddHostedService<ExtractWorker>();
builder.Services.AddHostedService<ConvertWorker>();
builder.Services.AddHostedService<ValidateWorker>();
builder.Services.AddHostedService<StoreWorker>();
builder.Services.AddHostedService<CleanupWorker>();

var host = builder.Build();
host.Run();