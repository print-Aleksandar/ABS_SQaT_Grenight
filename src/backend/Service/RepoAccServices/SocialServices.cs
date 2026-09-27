using Domain.Models;
using Repository.Data;
using Repository.Repositories;

namespace Service.RepoAccServices;

public class SocialServices : ISocialServices
{
    private readonly ISocialRepository _socialRepository;
    private readonly ApplicationDbContext _db;

    public SocialServices(ISocialRepository socialRepository, ApplicationDbContext db)
    {
        _socialRepository = socialRepository;
        _db = db;
    }
    
    public async Task<PagedResult<Player>> GetNonFriends(Guid forPlayerId, bool onlineOnly, bool ascOrder, int pageNumber, int pageSize)
    {
        var player = await _socialRepository.GetPlayerById(forPlayerId);

        if (player != null)
        {
            return await _socialRepository.GetPlayersAsync(forPlayerId, false, onlineOnly, ascOrder, pageNumber, pageSize);
        }
        
        throw new InvalidOperationException($"[SocialServices.GetNonFriends] Player not found. forPlayerId={forPlayerId}");
    }

    public async Task<PagedResult<Player>> GetFriends(Guid forPlayerId, bool onlineOnly, bool ascOrder, int pageNumber, int pageSize)
    {
        var player = await _socialRepository.GetPlayerById(forPlayerId);

        if (player != null)
        {
            return await _socialRepository.GetPlayersAsync(forPlayerId, true, onlineOnly, ascOrder, pageNumber, pageSize);
        }
        
        throw new InvalidOperationException($"[SocialServices.GetFriends] Player not found. forPlayerId={forPlayerId}");
    }

    public async Task SendFriendRequest(Guid fromPlayerId, Guid toPlayerId)
    {
        if (fromPlayerId == toPlayerId)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Cannot send friend request to self. playerId={fromPlayerId}");
        }

        var fromPlayer = await _socialRepository.GetPlayerById(fromPlayerId);
        if (fromPlayer == null)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Requester not found. fromPlayerId={fromPlayerId}");
        }

        var toPlayer = await _socialRepository.GetPlayerById(toPlayerId);
        if (toPlayer == null)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Receiver not found. toPlayerId={toPlayerId}");
        }

        var block = await _socialRepository.GetActiveBlockByParticipantsAsync(fromPlayerId, toPlayerId);
        if (block != null)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Active block exists between players. fromPlayerId={fromPlayerId}, toPlayerId={toPlayerId}, blockId={block.Id}");
        }

        var friendship = await _socialRepository.GetActiveFriendshipByParticipantsAsync(fromPlayerId, toPlayerId);
        if (friendship != null)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Active friendship already exists. fromPlayerId={fromPlayerId}, toPlayerId={toPlayerId}, friendshipId={friendship.Id}");
        }

        var friendRequest = await _socialRepository.GetActiveFriendshipRequestByParticipantsAsync(fromPlayerId, toPlayerId);
        if (friendRequest != null)
        {
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Active friendship request already exists. fromPlayerId={fromPlayerId}, toPlayerId={toPlayerId}, friendRequestId={friendRequest.Id}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            FriendshipRequest newFriendshipRequest = new FriendshipRequest()
            {
                IsActive = true,
                RequesterId = fromPlayerId,
                ReceiverId = toPlayerId
            };
            
            await _socialRepository.AddOrUpdateFriendshipRequestAsync(newFriendshipRequest);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.SendFriendRequest] Transaction failed. fromPlayerId={fromPlayerId}, toPlayerId={toPlayerId}", ex);
        }
    }

    public async Task AcceptFriendshipRequest(Guid friendRequestId, Guid receiverPlayerId)
    {
        var friendRequest = await _socialRepository.GetFriendshipRequestByIdAsync(friendRequestId);

        if (friendRequest == null)
        {
            throw new InvalidOperationException($"[SocialServices.AcceptFriendshipRequest] Friendship request not found. friendRequestId={friendRequestId}");
        }

        if (!friendRequest.IsActive)
        {
            throw new InvalidOperationException($"[SocialServices.AcceptFriendshipRequest] Friendship request is not active. friendRequestId={friendRequestId}, isActive={friendRequest.IsActive}");
        }

        if (receiverPlayerId != friendRequest.ReceiverId)
        {
            throw new InvalidOperationException($"[SocialServices.AcceptFriendshipRequest] Receiver mismatch. friendRequestId={friendRequestId}, receiverPlayerId={receiverPlayerId}, expectedReceiverId={friendRequest.ReceiverId}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            friendRequest.IsAccepted = true;
            friendRequest.IsActive = false;
            friendRequest.EndTs = DateTime.UtcNow;
            
            await _socialRepository.AddOrUpdateFriendshipRequestAsync(friendRequest);

            Friendship newFriendship = new Friendship
            {
                Friend1Id = friendRequest.RequesterId,
                Friend2Id = receiverPlayerId
            };
            
            await _socialRepository.AddOrUpdateFriendshipAsync(newFriendship);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.AcceptFriendshipRequest] Transaction failed. friendRequestId={friendRequestId}, receiverPlayerId={receiverPlayerId}", ex);
        }
    }

    public async Task DeclineFriendshipRequest(Guid friendRequestId, Guid receiverPlayerId)
    {
        var friendRequest = await _socialRepository.GetFriendshipRequestByIdAsync(friendRequestId);

        if (friendRequest == null)
        {
            throw new InvalidOperationException($"[SocialServices.DeclineFriendshipRequest] Friendship request not found. friendRequestId={friendRequestId}");
        }

        if (!friendRequest.IsActive)
        {
            throw new InvalidOperationException($"[SocialServices.DeclineFriendshipRequest] Friendship request is not active. friendRequestId={friendRequestId}, isActive={friendRequest.IsActive}");
        }

        if (receiverPlayerId != friendRequest.ReceiverId)
        {
            throw new InvalidOperationException($"[SocialServices.DeclineFriendshipRequest] Receiver mismatch. friendRequestId={friendRequestId}, receiverPlayerId={receiverPlayerId}, expectedReceiverId={friendRequest.ReceiverId}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            friendRequest.IsAccepted = false;
            friendRequest.IsActive = false;
            friendRequest.EndTs = DateTime.UtcNow;
            
            await _socialRepository.AddOrUpdateFriendshipRequestAsync(friendRequest);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.DeclineFriendshipRequest] Transaction failed. friendRequestId={friendRequestId}, receiverPlayerId={receiverPlayerId}", ex);
        }
    }

    public async Task EndFriendship(Guid friendshipId, Guid participantId)
    {
        var friendship = await _socialRepository.GetFriendshipByIdAsync(friendshipId);

        if (friendship == null)
        {
            throw new InvalidOperationException($"[SocialServices.EndFriendship] Friendship not found. friendshipId={friendshipId}");
        }

        if (!friendship.IsActive)
        {
            throw new InvalidOperationException($"[SocialServices.EndFriendship] Friendship is not active. friendshipId={friendshipId}, isActive={friendship.IsActive}");
        }

        if (friendship.Friend1Id != participantId && friendship.Friend2Id != participantId)
        {
            throw new InvalidOperationException($"[SocialServices.EndFriendship] Participant is not part of the friendship. friendshipId={friendshipId}, participantId={participantId}, friend1Id={friendship.Friend1Id}, friend2Id={friendship.Friend2Id}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            friendship.IsActive = false;
            friendship.EndTs = DateTime.UtcNow;
            
            await _socialRepository.AddOrUpdateFriendshipAsync(friendship);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.EndFriendship] Transaction failed. friendshipId={friendshipId}, participantId={participantId}", ex);
        }
    }

    public async Task BlockPlayer(Guid blockerId, Guid blockedId)
    {
        if (blockerId == blockedId)
        {
            throw new InvalidOperationException($"[SocialServices.BlockPlayer] Cannot block self. playerId={blockerId}");
        }

        var blocker = await _socialRepository.GetPlayerById(blockerId);
        if (blocker == null)
        {
            throw new InvalidOperationException($"[SocialServices.BlockPlayer] Blocker not found. blockerId={blockerId}");
        }

        var blocked = await _socialRepository.GetPlayerById(blockedId);
        if (blocked == null)
        {
            throw new InvalidOperationException($"[SocialServices.BlockPlayer] Blocked player not found. blockedId={blockedId}");
        }

        var alreadyBlock = await _socialRepository.GetActiveBlockByParticipantsAsync(blockerId, blockedId);
        if (alreadyBlock != null)
        {
            throw new InvalidOperationException($"[SocialServices.BlockPlayer] Active block already exists. blockerId={blockerId}, blockedId={blockedId}, blockId={alreadyBlock.Id}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            var friendship = await _socialRepository.GetActiveFriendshipByParticipantsAsync(blockerId, blockedId);
            if (friendship != null)
            {
                friendship.IsActive = false;
                friendship.EndTs = DateTime.UtcNow;
                await _socialRepository.AddOrUpdateFriendshipAsync(friendship);
            }

            var friendshipRequest = await _socialRepository.GetActiveFriendshipRequestByParticipantsAsync(blockerId, blockedId);
            if (friendshipRequest != null)
            {
                friendshipRequest.IsActive = false;
                friendshipRequest.EndTs = DateTime.UtcNow;
                await _socialRepository.AddOrUpdateFriendshipRequestAsync(friendshipRequest);
            }

            Block newBlock = new Block
            {
                BlockerId = blockerId,
                BlockedId = blockedId
            };
            
            await _socialRepository.AddOrUpdateBlockAsync(newBlock);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.BlockPlayer] Transaction failed. blockerId={blockerId}, blockedId={blockedId}", ex);
        }
    }

    public async Task UnblockPlayer(Guid blockerId, Guid blockedId)
    {
        var block = await _socialRepository.GetActiveBlockByParticipantsAsync(blockerId, blockedId);

        if (block == null)
        {
            throw new InvalidOperationException($"[SocialServices.UnblockPlayer] Active block not found. blockerId={blockerId}, blockedId={blockedId}");
        }

        if (block.BlockerId != blockerId || block.BlockedId != blockedId)
        {
            throw new InvalidOperationException($"[SocialServices.UnblockPlayer] Only the blocker can unblock. blockerId={blockerId}, blockedId={blockedId}, actualBlockerId={block.BlockerId}, actualBlockedId={block.BlockedId}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            block.IsActive = false;
            block.EndTs = DateTime.UtcNow;
            await _socialRepository.AddOrUpdateBlockAsync(block);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[SocialServices.UnblockPlayer] Transaction failed. blockerId={blockerId}, blockedId={blockedId}", ex);
        }
    }
}