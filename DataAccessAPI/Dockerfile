# Use the official .NET SDK image to build and publish the app
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY . .
RUN dotnet restore "DataAccessAPI.csproj"
RUN dotnet publish "DataAccessAPI.csproj" -c Release -o /app/publish

# Use the official ASP.NET runtime image for the final container
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
EXPOSE 8080
ENTRYPOINT ["dotnet", "DataAccessAPI.dll"]
