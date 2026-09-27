using Domain.Models;

namespace Service.RepoAccServices;

public interface IGameServices
{
    Task<PagedResult<Game>> GetGames(Guid? player1Id, Guid? player2Id, int pageNumber, int pageSize);
    
    Task SendGameRequest(Guid fromPlayerId, Guid? toPlayerId, bool isPvpRequest);

    Task DecideGameRequest(Guid gameRequestId, Guid receiverPlayerId, bool decision);
    
    Task RevokeGameRequest(Guid gameRequestId, Guid requesterPlayerId);

    Task ForfeitGame(Guid gameId, Guid participantId);

    Task AddApiRequest(Guid gameId, Guid fromPlayerId, string pieceUid, short y, short x);

    Task AddApiResponse(Guid apiRequestId, string status, string message);
}