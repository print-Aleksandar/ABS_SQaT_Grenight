using Domain.Models;

namespace Service.RepoAccServices;

public interface ISocialServices
{
    Task<PagedResult<Player>> GetNonFriends(Guid forPlayerId, bool onlineOnly, bool ascOrder, int pageNumber, int pageSize);
    
    Task<PagedResult<Player>> GetFriends(Guid fromPlayerId, bool onlineOnly, bool ascOrder, int pageNumber, int pageSize);
    
    Task SendFriendRequest(Guid fromPlayerId, Guid toPlayerId);
    
    Task AcceptFriendshipRequest(Guid friendRequestId, Guid receiverPlayerId);
    
    Task DeclineFriendshipRequest(Guid friendRequestId, Guid receiverPlayerId);
    
    Task EndFriendship(Guid friendshipId, Guid participantId);
    
    Task BlockPlayer(Guid blockerId, Guid blockedId);
    
    Task UnblockPlayer(Guid blockerId, Guid blockedId);
}