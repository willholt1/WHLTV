FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

COPY ["WHLTV/WHLTV.Pipeline/src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj", "WHLTV/WHLTV.Pipeline/src/WHLTV.DemoPipeline.Worker/"]
COPY ["WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.Domain/WHLTV.Pipeline.Domain.csproj", "WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.Domain/"]
COPY ["WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.DataAccess/WHLTV.Pipeline.DataAccess.csproj", "WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.DataAccess/"]
COPY ["WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.Infrastructure/WHLTV.Pipeline.Infrastructure.csproj", "WHLTV/WHLTV.Pipeline/src/WHLTV.Pipeline.Infrastructure/"]
RUN dotnet restore "WHLTV/WHLTV.Pipeline/src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj"

COPY . .
RUN dotnet publish "WHLTV/WHLTV.Pipeline/src/WHLTV.DemoPipeline.Worker/WHLTV.DemoPipeline.Worker.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/runtime:10.0 AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends unrar 7zip libgssapi-krb5-2 python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pyenv \
    && /opt/pyenv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/pyenv/bin/pip install --no-cache-dir demoparser2 pandas pyarrow

COPY WHLTV/DemoParser /app/python/DemoParser
COPY WHLTV/models /app/python/models
COPY awpyParquet /app/python/awpyParquet

RUN /opt/pyenv/bin/pip install --no-cache-dir /app/python/awpyParquet

ENV PATH=/opt/pyenv/bin:$PATH
ENV PYTHONPATH=/app/python

COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "WHLTV.DemoPipeline.Worker.dll"]
