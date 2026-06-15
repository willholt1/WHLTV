FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj", "src/WHLTV.DemoPipeline.Worker/"]
COPY ["src/WHLTV.Pipeline.Domain/WHLTV.Pipeline.Domain.csproj", "src/WHLTV.Pipeline.Domain/"]
COPY ["src/WHLTV.Pipeline.DataAccess/WHLTV.Pipeline.DataAccess.csproj", "src/WHLTV.Pipeline.DataAccess/"]
COPY ["src/WHLTV.Pipeline.Infrastructure/WHLTV.Pipeline.Infrastructure.csproj", "src/WHLTV.Pipeline.Infrastructure/"]
RUN dotnet restore "src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj"

COPY . .
RUN dotnet publish "src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/runtime:10.0 AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends p7zip-full libgssapi-krb5-2 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "WHLTV.DemoPipeline.Worker.dll"]
