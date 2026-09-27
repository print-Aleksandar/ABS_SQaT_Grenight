using Domain.Models;
using Microsoft.EntityFrameworkCore;
using Repository.Data;

namespace Repository.Repositories;

public class GameRepository : IGameRepository
{
    private readonly ApplicationDbContext _db;

    public GameRepository(ApplicationDbContext db)
    {
        _db = db;
    }

    public async Task<PagedResult<Game>> GetGamesAsync(Guid? player1Id, Guid? player2Id, int pageNumber = 1, int pageSize = 20)
    {
        pageNumber = pageNumber < 1 ? 1 : pageNumber;
        pageSize = pageSize switch
        {
            < 1 => 10,
            > 100 => 100,
            _ => pageSize
        };

        IQueryable<Game> query = _db.Games
            .AsNoTracking()
            .Include(g => g.GameRequest)
                .ThenInclude(gr => gr.Requester)
            .Include(g => g.GameRequest)
                .ThenInclude(gr => gr.Receiver);

        if (player1Id.HasValue && player2Id.HasValue)
        {
            var p1 = player1Id.Value;
            var p2 = player2Id.Value;

            query = query.Where(g =>
                (g.GameRequest.RequesterId == p1 && g.GameRequest.ReceiverId == p2) ||
                (g.GameRequest.RequesterId == p2 && g.GameRequest.ReceiverId == p1));
        }
        else if (player1Id.HasValue)
        {
            var p1 = player1Id.Value;
            query = query.Where(g => g.GameRequest.RequesterId == p1 || g.GameRequest.ReceiverId == p1);
        }
        else if (player2Id.HasValue)
        {
            var p2 = player2Id.Value;
            query = query.Where(g => g.GameRequest.RequesterId == p2 || g.GameRequest.ReceiverId == p2);
        }

        int totalCount = await query.CountAsync();

        var items = await query
            .OrderByDescending(g => g.StartTs)
            .Skip((pageNumber - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();

        return new PagedResult<Game>
        {
            Items = items,
            TotalCount = totalCount,
            PageNumber = pageNumber,
            PageSize = pageSize
        };
    }

    public async Task<Game?> GetActiveGameForPlayerAsync(Guid playerId)
    {
        return await _db.Games
            .AsNoTracking()
            .Include(g => g.GameRequest)
            .FirstOrDefaultAsync(g => g.IsActive 
                && (g.GameRequest.RequesterId == playerId || g.GameRequest.ReceiverId == playerId));
    }

    public async Task AddOrUpdateGameRequestAsync(GameRequest gameRequest)
    {
        var exists = gameRequest.Id != Guid.Empty && await _db.GameRequests.AnyAsync(gr => gr.Id == gameRequest.Id);

        if (!exists)
        {
            await _db.GameRequests.AddAsync(gameRequest);
        }
        else
        {
            _db.GameRequests.Update(gameRequest);
        }

        await _db.SaveChangesAsync();
    }

    public async Task AddOrUpdateGameAsync(Game game)
    {
        var exists = game.Id != Guid.Empty && await _db.Games.AnyAsync(g => g.Id == game.Id);

        if (!exists)
        {
            await _db.Games.AddAsync(game);
        }
        else
        {
            _db.Games.Update(game);
        }

        await _db.SaveChangesAsync();
    }

    public async Task AddOrUpdateApiRequestAsync(ApiRequest apiRequest)
    {
        var exists = apiRequest.Id != Guid.Empty && await _db.ApiRequests.AnyAsync(r => r.Id == apiRequest.Id);

        if (!exists)
        {
            await _db.ApiRequests.AddAsync(apiRequest);
        }
        else
        {
            _db.ApiRequests.Update(apiRequest);
        }

        await _db.SaveChangesAsync();
    }

    public async Task AddOrUpdateApiResponseAsync(ApiResponse apiResponse)
    {
        var exists = apiResponse.Id != Guid.Empty && await _db.ApiResponses.AnyAsync(r => r.Id == apiResponse.Id);

        if (!exists)
        {
            await _db.ApiResponses.AddAsync(apiResponse);
        }
        else
        {
            _db.ApiResponses.Update(apiResponse);
        }

        await _db.SaveChangesAsync();
    }

    public async Task<Game?> GetGameByIdAsync(Guid gameId)
    {
        return await _db.Games
            .Include(g => g.GameRequest)
            .FirstOrDefaultAsync(g => g.Id == gameId);
    }

    public async Task<GameRequest?> GetGameRequestByIdAsync(Guid gameRequestId)
    {
        return await _db.GameRequests.FindAsync(gameRequestId);
    }

    public async Task<ApiRequest?> GetApiRequestByIdAsync(Guid apiRequestId)
    {
        return await _db.ApiRequests.FindAsync(apiRequestId);
    }

    public async Task<ApiResponse?> GetApiResponseByIdAsync(Guid apiResponseId)
    {
        return await _db.ApiResponses.FindAsync(apiResponseId);
    }
}