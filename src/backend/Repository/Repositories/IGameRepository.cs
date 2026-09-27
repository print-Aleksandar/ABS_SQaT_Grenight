using Domain.Models;

namespace Repository.Repositories;

public interface IGameRepository
{
    Task<PagedResult<Game>> GetGamesAsync(Guid? player1Id, Guid? player2Id, int pageNumber, int pageSize);
    
    Task AddOrUpdateGameRequestAsync(GameRequest gameRequest);
    
    Task AddOrUpdateGameAsync(Game game);
    
    Task AddOrUpdateApiRequestAsync(ApiRequest apiRequest);
    
    Task AddOrUpdateApiResponseAsync(ApiResponse apiResponse);
    
    Task<Game?> GetGameByIdAsync(Guid gameId);
    Task<GameRequest?> GetGameRequestByIdAsync(Guid gameRequestId);
    Task<ApiRequest?> GetApiRequestByIdAsync(Guid apiRequestId);
    Task<ApiResponse?> GetApiResponseByIdAsync(Guid apiResponseId);
    
    Task<Game?> GetActiveGameForPlayerAsync(Guid forPlayerId);
}