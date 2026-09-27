using Domain.Models;
using Repository.Data;
using Repository.Repositories;

namespace Service.RepoAccServices;

public class GameServices : IGameServices
{
    private readonly IGameRepository _gameRepository;
    private readonly ISocialRepository _socialRepository;
    private readonly ApplicationDbContext _db;

    public GameServices(IGameRepository gameRepository, ISocialRepository socialRepository, ApplicationDbContext db)
    {
        _gameRepository = gameRepository;
        _socialRepository = socialRepository;
        _db = db;
    }

    public async Task<PagedResult<Game>> GetGames(Guid? player1Id, Guid? player2Id, int pageNumber, int pageSize)
    {
        return await _gameRepository.GetGamesAsync(player1Id, player2Id, pageNumber, pageSize);
    }

    public async Task SendGameRequest(Guid fromPlayerId, Guid? toPlayerId, bool isPvpRequest)
    {
        var requester = await _socialRepository.GetPlayerById(fromPlayerId);

        if (requester == null)
        {
            throw new InvalidOperationException($"[GameServices.SendGameRequest] Requester not found. fromPlayerId={fromPlayerId}");
        }

        if (!requester.IsOnline)
        {
            throw new InvalidOperationException($"[GameServices.SendGameRequest] Requester is not online. fromPlayerId={fromPlayerId}");
        }

        if (requester.IsInGame)
        {
            throw new InvalidOperationException($"[GameServices.SendGameRequest] Requester is already in a game. fromPlayerId={fromPlayerId}");
        }

        if (isPvpRequest)
        {
            if (!toPlayerId.HasValue)
            {
                throw new InvalidOperationException($"[GameServices.SendGameRequest] PvP request requires a receiver. fromPlayerId={fromPlayerId}");
            }

            if (fromPlayerId == toPlayerId.Value)
            {
                throw new InvalidOperationException($"[GameServices.SendGameRequest] Cannot send PvP request to self. fromPlayerId={fromPlayerId}");
            }

            var receiver = await _socialRepository.GetPlayerById(toPlayerId.Value);

            if (receiver == null)
            {
                throw new InvalidOperationException($"[GameServices.SendGameRequest] Receiver not found. toPlayerId={toPlayerId.Value}");
            }

            if (!receiver.IsOnline)
            {
                throw new InvalidOperationException($"[GameServices.SendGameRequest] Receiver is not online. toPlayerId={toPlayerId.Value}");
            }

            if (receiver.IsInGame)
            {
                throw new InvalidOperationException($"[GameServices.SendGameRequest] Receiver is already in a game. toPlayerId={toPlayerId.Value}");
            }
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            GameRequest newGameRequest = new GameRequest
            {
                IsAccepted = isPvpRequest ? null : true,
                RequesterId = fromPlayerId,
                ReceiverId = isPvpRequest ? toPlayerId : null,
                IsPvpRequest = isPvpRequest,
                IsActive = isPvpRequest,
                EndTs = isPvpRequest ? null : DateTime.UtcNow
            };

            await _gameRepository.AddOrUpdateGameRequestAsync(newGameRequest);

            if (!isPvpRequest)
            {
                Game pveGame = new Game
                {
                    IsPvp = false,
                    GameRequest = newGameRequest
                };

                await _gameRepository.AddOrUpdateGameAsync(pveGame);
            }

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.SendGameRequest] Transaction failed. fromPlayerId={fromPlayerId}, toPlayerId={toPlayerId}, isPvpRequest={isPvpRequest}", ex);
        }
    }

    public async Task DecideGameRequest(Guid gameRequestId, Guid receiverPlayerId, bool decision)
    {
        var gameRequest = await _gameRepository.GetGameRequestByIdAsync(gameRequestId);

        if (gameRequest == null)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Game request not found. gameRequestId={gameRequestId}");
        }

        if (!gameRequest.IsPvpRequest)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Not a PvP request. gameRequestId={gameRequestId}, isPvpRequest={gameRequest.IsPvpRequest}");
        }

        if (gameRequest.ReceiverId != receiverPlayerId)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Receiver mismatch. gameRequestId={gameRequestId}, receiverPlayerId={receiverPlayerId}, expectedReceiverId={gameRequest.ReceiverId}");
        }

        if (!gameRequest.IsActive)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Request is not active. gameRequestId={gameRequestId}, isActive={gameRequest.IsActive}");
        }

        var requester = await _socialRepository.GetPlayerById(gameRequest.RequesterId);
        if (requester == null)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Requester not found. requesterId={gameRequest.RequesterId}");
        }

        if (!requester.IsOnline)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Requester is not online. requesterId={gameRequest.RequesterId}");
        }

        if (requester.IsInGame)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Requester is already in a game. requesterId={gameRequest.RequesterId}");
        }

        if (!gameRequest.ReceiverId.HasValue)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Receiver is missing on PvP request. gameRequestId={gameRequestId}");
        }

        var receiver = await _socialRepository.GetPlayerById(gameRequest.ReceiverId.Value);
        if (receiver == null)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Receiver not found. receiverId={gameRequest.ReceiverId.Value}");
        }

        if (!receiver.IsOnline)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Receiver is not online. receiverId={gameRequest.ReceiverId.Value}");
        }

        if (receiver.IsInGame)
        {
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Receiver is already in a game. receiverId={gameRequest.ReceiverId.Value}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            gameRequest.IsAccepted = decision;
            gameRequest.IsActive = false;
            gameRequest.EndTs = DateTime.UtcNow;

            await _gameRepository.AddOrUpdateGameRequestAsync(gameRequest);

            if (decision)
            {
                requester.IsInGame = true;
                await _socialRepository.UpdatePlayer(requester);

                receiver.IsInGame = true;
                await _socialRepository.UpdatePlayer(receiver);

                Game newGame = new Game
                {
                    IsActive = true,
                    IsWhiteOnTurn = true,
                    GameRequestId = gameRequest.Id,
                    IsPvp = gameRequest.IsPvpRequest,
                };

                await _gameRepository.AddOrUpdateGameAsync(newGame);
            }

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.DecideGameRequest] Transaction failed. gameRequestId={gameRequestId}, receiverPlayerId={receiverPlayerId}, decision={decision}", ex);
        }
    }

    public async Task RevokeGameRequest(Guid gameRequestId, Guid requesterPlayerId)
    {
        var gameRequest = await _gameRepository.GetGameRequestByIdAsync(gameRequestId);

        if (gameRequest == null)
        {
            throw new InvalidOperationException($"[GameServices.RevokeGameRequest] Game request not found. gameRequestId={gameRequestId}");
        }

        if (!gameRequest.IsPvpRequest)
        {
            throw new InvalidOperationException($"[GameServices.RevokeGameRequest] Not a PvP request. gameRequestId={gameRequestId}, isPvpRequest={gameRequest.IsPvpRequest}");
        }

        if (gameRequest.RequesterId != requesterPlayerId)
        {
            throw new InvalidOperationException($"[GameServices.RevokeGameRequest] Requester mismatch. gameRequestId={gameRequestId}, requesterPlayerId={requesterPlayerId}, expectedRequesterId={gameRequest.RequesterId}");
        }

        if (!gameRequest.IsActive)
        {
            throw new InvalidOperationException($"[GameServices.RevokeGameRequest] Request is not active. gameRequestId={gameRequestId}, isActive={gameRequest.IsActive}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            gameRequest.IsActive = false;
            gameRequest.EndTs = DateTime.UtcNow;

            await _gameRepository.AddOrUpdateGameRequestAsync(gameRequest);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.RevokeGameRequest] Transaction failed. gameRequestId={gameRequestId}, requesterPlayerId={requesterPlayerId}", ex);
        }
    }

    public async Task ForfeitGame(Guid gameId, Guid participantId)
    {
        var game = await _gameRepository.GetGameByIdAsync(gameId);

        if (game == null)
        {
            throw new InvalidOperationException($"[GameServices.ForfeitGame] Game not found. gameId={gameId}");
        }

        if (!game.IsActive)
        {
            throw new InvalidOperationException($"[GameServices.ForfeitGame] Game is not active. gameId={gameId}, isActive={game.IsActive}");
        }

        if (game.GameRequest == null)
        {
            throw new InvalidOperationException($"[GameServices.ForfeitGame] Game has no associated GameRequest. gameId={gameId}");
        }

        if (game.GameRequest.RequesterId != participantId && game.GameRequest.ReceiverId != participantId)
        {
            throw new InvalidOperationException($"[GameServices.ForfeitGame] Participant is not part of the game. gameId={gameId}, participantId={participantId}, requesterId={game.GameRequest.RequesterId}, receiverId={game.GameRequest.ReceiverId}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            var isWhiteWinner = game.GameRequest.RequesterId != participantId;

            game.IsWhiteWinner = isWhiteWinner;
            game.IsDraw = false;
            game.EndTs = DateTime.UtcNow;
            game.IsActive = false;

            await _gameRepository.AddOrUpdateGameAsync(game);

            if (game.IsPvp)
            {
                if (!game.GameRequest.ReceiverId.HasValue)
                {
                    throw new InvalidOperationException($"[GameServices.ForfeitGame] PvP game has no receiver. gameId={gameId}, gameRequestId={game.GameRequestId}");
                }

                var winnerId = isWhiteWinner ? game.GameRequest.RequesterId : game.GameRequest.ReceiverId.Value;
                var loserId = game.GameRequest.RequesterId == winnerId ? game.GameRequest.ReceiverId.Value : game.GameRequest.RequesterId;

                var winner = await _socialRepository.GetPlayerById(winnerId);
                if (winner == null)
                {
                    throw new InvalidOperationException($"[GameServices.ForfeitGame] Winner not found. gameId={gameId}, winnerId={winnerId}");
                }

                var loser = await _socialRepository.GetPlayerById(loserId);
                if (loser == null)
                {
                    throw new InvalidOperationException($"[GameServices.ForfeitGame] Loser not found. gameId={gameId}, loserId={loserId}");
                }

                winner.Points += 8;
                loser.Points -= 8;

                if (loser.Points < 0)
                {
                    loser.Points = 0;
                }

                winner.IsInGame = false;
                loser.IsInGame = false;

                await _socialRepository.UpdatePlayer(winner);
                await _socialRepository.UpdatePlayer(loser);
            }
            else
            {
                var player = await _socialRepository.GetPlayerById(participantId);
                if (player == null)
                {
                    throw new InvalidOperationException($"[GameServices.ForfeitGame] Player not found. gameId={gameId}, participantId={participantId}");
                }

                player.Points -= 8;
                if (player.Points < 0)
                {
                    player.Points = 0;
                }

                player.IsInGame = false;

                await _socialRepository.UpdatePlayer(player);
            }

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.ForfeitGame] Transaction failed. gameId={gameId}, participantId={participantId}", ex);
        }
    }

    public async Task AddApiRequest(Guid gameId, Guid fromPlayerId, string pieceUid, short y, short x)
    {
        var game = await _gameRepository.GetGameByIdAsync(gameId);

        if (game == null)
        {
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Game not found. gameId={gameId}");
        }

        if (!game.IsActive)
        {
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Game is not active. gameId={gameId}, isActive={game.IsActive}");
        }

        if (game.GameRequest == null)
        {
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Game has no associated GameRequest. gameId={gameId}");
        }

        if (game.GameRequest.RequesterId != fromPlayerId && game.GameRequest.ReceiverId != fromPlayerId)
        {
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Player is not part of the game. gameId={gameId}, fromPlayerId={fromPlayerId}, requesterId={game.GameRequest.RequesterId}, receiverId={game.GameRequest.ReceiverId}");
        }

        var isWhitePlayer = game.GameRequest.RequesterId == fromPlayerId;
        if (game.IsWhiteOnTurn != isWhitePlayer)
        {
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Not the player's turn. gameId={gameId}, fromPlayerId={fromPlayerId}, isWhiteOnTurn={game.IsWhiteOnTurn}, isWhitePlayer={isWhitePlayer}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            ApiRequest newApiRequest = new ApiRequest
            {
                GameId = game.Id,
                FromPlayerId = fromPlayerId,
                PieceUid = pieceUid,
                X = x,
                Y = y,
                IsSent = false
            };

            await _gameRepository.AddOrUpdateApiRequestAsync(newApiRequest);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.AddApiRequest] Transaction failed. gameId={gameId}, fromPlayerId={fromPlayerId}, pieceUid={pieceUid}", ex);
        }
    }

    public async Task AddApiResponse(Guid apiRequestId, string status, string message)
    {
        var apiRequest = await _gameRepository.GetApiRequestByIdAsync(apiRequestId);

        if (apiRequest == null)
        {
            throw new InvalidOperationException($"[GameServices.AddApiResponse] ApiRequest not found. apiRequestId={apiRequestId}");
        }

        var game = await _gameRepository.GetGameByIdAsync(apiRequest.GameId);
        if (game == null)
        {
            throw new InvalidOperationException($"[GameServices.AddApiResponse] Game not found for ApiRequest. apiRequestId={apiRequestId}, gameId={apiRequest.GameId}");
        }

        if (!game.IsActive)
        {
            throw new InvalidOperationException($"[GameServices.AddApiResponse] Game is not active. apiRequestId={apiRequestId}, gameId={apiRequest.GameId}, isActive={game.IsActive}");
        }

        await using var tx = await _db.Database.BeginTransactionAsync();
        try
        {
            ApiResponse newApiResponse = new ApiResponse
            {
                ApiRequestId = apiRequestId,
                Status = status,
                Message = message
            };

            await _gameRepository.AddOrUpdateApiResponseAsync(newApiResponse);

            await tx.CommitAsync();
        }
        catch (Exception ex)
        {
            await tx.RollbackAsync();
            throw new InvalidOperationException($"[GameServices.AddApiResponse] Transaction failed. apiRequestId={apiRequestId}, status={status}", ex);
        }
    }
}