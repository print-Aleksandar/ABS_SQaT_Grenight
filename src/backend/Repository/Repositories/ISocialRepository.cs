using Domain.Models;

namespace Repository.Repositories;

public interface ISocialRepository
{
    Task<Player?> GetPlayerById(Guid playerId);

    Task<PagedResult<Player>> GetPlayersAsync(Guid forPlayerId, bool selectFriends, bool onlyOnline, bool ascOrder,
        int pageNumber, int pageSize);

    Task<FriendshipRequest?> GetActiveFriendshipRequestByParticipantsAsync(Guid participant1Id, Guid participant2Id);
    Task<Friendship?> GetActiveFriendshipByParticipantsAsync(Guid friend1Id, Guid friend2Id);
    Task<Block?> GetActiveBlockByParticipantsAsync(Guid participant1Id, Guid participant2Id);
    
    Task<FriendshipRequest?> GetFriendshipRequestByIdAsync(Guid friendRequestId);
    Task<Friendship?> GetFriendshipByIdAsync(Guid friendshipId);
    Task<Block?> GetBlockByIdAsync(Guid blockId);
    
    Task AddOrUpdateFriendshipRequestAsync(FriendshipRequest friendshipRequest);
    Task AddOrUpdateFriendshipAsync(Friendship friendship);
    Task AddOrUpdateBlockAsync(Block block);
    Task UpdatePlayer(Player player);
}