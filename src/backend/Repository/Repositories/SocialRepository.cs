using Domain.Models;
using Microsoft.EntityFrameworkCore;
using Repository.Data;

namespace Repository.Repositories;

public class SocialRepository : ISocialRepository
{
    private readonly ApplicationDbContext _db;

    public SocialRepository(ApplicationDbContext db)
    {
        _db = db;
    }
    
    public async Task<Player?> GetPlayerById(Guid playerId)
    {
        return await _db.Users
            .FindAsync(playerId);
    }

    public async Task<PagedResult<Player>> GetPlayersAsync(Guid forPlayerId, bool selectFriends, bool onlyOnline, bool ascOrder,
        int pageNumber = 1, int pageSize = 20)
    {
        pageNumber = pageNumber < 1 ? 1 : pageNumber;
        pageSize = pageSize switch
        {
            < 1 => 10,
            > 100 => 100,
            _ => pageSize
        };
    
        IQueryable<Player> query = _db.Users.AsNoTracking().Where(p => p.Id != forPlayerId);
    
        var blockedPlayerIds = _db.Set<Block>()
            .Where(b => b.IsActive && (b.BlockerId == forPlayerId || b.BlockedId == forPlayerId))
            .Select(b => b.BlockerId == forPlayerId ? b.BlockedId : b.BlockerId);
    
        query = query.Where(p => !blockedPlayerIds.Contains(p.Id));
    
        if (onlyOnline)
        {
            query = query.Where(p => p.IsOnline);
        }
    
        var friendIds = _db.Friendships
            .Where(f => f.IsActive && (f.Friend1Id == forPlayerId || f.Friend2Id == forPlayerId))
            .Select(f => f.Friend1Id == forPlayerId ? f.Friend2Id : f.Friend1Id);
    
        if (selectFriends)
        {
            query = query.Where(p => friendIds.Contains(p.Id));
        }
        else
        {
            query = query.Where(p => !friendIds.Contains(p.Id));
        }
    
        int totalCount = await query.CountAsync();

        var orderedQuery = query.OrderByDescending(p => p.IsOnline);

        query = ascOrder 
            ? orderedQuery.ThenBy(p => p.Points) 
            : orderedQuery.ThenByDescending(p => p.Points);

        var items = await query
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return new PagedResult<Player>
        {
            Items = items,
            TotalCount = totalCount,
            PageNumber = pageNumber,
            PageSize = pageSize
        };
    }

    public async Task<FriendshipRequest?> GetActiveFriendshipRequestByParticipantsAsync(Guid participant1Id, Guid participant2Id)
    {
        return await _db.FriendshipRequests
            .FirstOrDefaultAsync(fr => fr.IsActive && 
                                       ((fr.RequesterId == participant1Id && fr.ReceiverId == participant2Id) ||
                                        (fr.RequesterId == participant2Id && fr.ReceiverId == participant1Id)));
    }

    public async Task<Friendship?> GetActiveFriendshipByParticipantsAsync(Guid friend1Id, Guid friend2Id)
    {
        return await _db.Friendships
            .FirstOrDefaultAsync(f => f.IsActive && 
                                       ((f.Friend1Id == friend1Id && f.Friend2Id == friend2Id) ||
                                        (f.Friend2Id == friend1Id && f.Friend1Id == friend2Id)));
    }

    public async Task<Block?> GetActiveBlockByParticipantsAsync(Guid participant1Id, Guid participant2Id)
    {
        return await _db.Blocks
            .FirstOrDefaultAsync(b => b.IsActive && 
                                       ((b.BlockerId == participant1Id && b.BlockedId == participant2Id) ||
                                        (b.BlockerId == participant2Id && b.BlockedId == participant1Id)));
    }

    public async Task<FriendshipRequest?> GetFriendshipRequestByIdAsync(Guid friendRequestId)
    {
        return await _db.FriendshipRequests
            .FindAsync(friendRequestId);
    }

    public async Task<Friendship?> GetFriendshipByIdAsync(Guid friendshipId)
    {
        return await _db.Friendships
            .FindAsync(friendshipId);
    }

    public async Task<Block?> GetBlockByIdAsync(Guid blockId)
    {
        return await _db.Blocks
            .FindAsync(blockId);
    }

    public async Task AddOrUpdateFriendshipRequestAsync(FriendshipRequest friendshipRequest)
    {
        var existing = await GetFriendshipRequestByIdAsync(friendshipRequest.Id);

        if (existing != null)
        { 
            _db.FriendshipRequests.Update(friendshipRequest);
        }
        else
        { 
            _db.FriendshipRequests.Add(friendshipRequest);
        }
        
        await _db.SaveChangesAsync();
    }

    public async Task AddOrUpdateFriendshipAsync(Friendship friendship)
    {
        var existing = await GetFriendshipByIdAsync(friendship.Id);

        if (existing != null)
        { 
            _db.Friendships.Update(friendship);
        }
        else
        { 
            _db.Friendships.Add(friendship);
        }
        
        await _db.SaveChangesAsync();
    }

    public async Task AddOrUpdateBlockAsync(Block block)
    {
        var existing = await GetBlockByIdAsync(block.Id);

        if (existing != null)
        { 
            _db.Blocks.Update(block);
        }
        else
        { 
            _db.Blocks.Add(block);
        }
        
        await _db.SaveChangesAsync();
    }

    public async Task UpdatePlayer(Player player)
    {
        var existing = await GetPlayerById(player.Id);

        if (existing != null)
        { 
            _db.Users.Update(player);
            await _db.SaveChangesAsync();
            return;
        }

        throw new InvalidOperationException("Player not found");
    }
}