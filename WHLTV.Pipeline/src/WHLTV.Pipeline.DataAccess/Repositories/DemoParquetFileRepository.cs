using Dapper;
using WHLTV.Pipeline.DataAccess.Connection;
using WHLTV.Pipeline.Domain.Jobs;
using WHLTV.Pipeline.Domain.Enums;

namespace WHLTV.Pipeline.DataAccess.Repositories;

public sealed class DemoParquetFileRepository
{
    private readonly DbConnectionFactory _connectionFactory;

    public DemoParquetFileRepository(DbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task CreateDemoParquetFile(int demoConversionJobID, Map demoMap, string patchVersion, string parquetTempRelativePath)
    {
        const string sql = """
            WITH mm as (
                SELECT tmm.matchmapid, tdcj.democonversionjobid
                FROM tbldemoconversionjobs tdcj
                INNER JOIN tbldemodownloadjobs tddj on tddj.demodownloadjobid = tdcj.demodownloadjobid
                INNER JOIN tblmatchmaps tmm on tmm.matchid = tddj.matchid and tmm.mapid = @DemoMapID
                WHERE tdcj.democonversionjobid = @DemoConversionJobID
            )
            INSERT INTO tbldemoparquetfiles (democonversionjobid
                                            ,matchmapid
                                            ,patchversion
                                            ,parquettemprelativepath
            )
            SELECT mm.democonversionjobid
                    ,mm.matchmapid
                    ,@PatchVersion
                    ,@ParquetTempRelativePath
            FROM mm;
            """;

        using var connection = _connectionFactory.CreateConnection();

        await connection.ExecuteAsync(sql, new
        {
            DemoConversionJobID = demoConversionJobID,
            DemoMapID = (int)demoMap,
            PatchVersion = patchVersion,
            ParquetTempRelativePath = parquetTempRelativePath
        });
    }
}