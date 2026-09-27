using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Identity;

namespace Domain.Models
{
    public abstract class BaseModel
    {
        public Guid Id { get; set; } = Guid.NewGuid();
    }

    public abstract class LoggedModel : BaseModel
    {
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    }

    public abstract class PeriodicalModel : BaseModel
    {
        public DateTime StartTs { get; set; } = DateTime.UtcNow;
        public DateTime? EndTs { get; set; }
        public bool IsActive { get; set; } = true;
    }

    public class Player : IdentityUser<Guid>
    {
        public DateTime Timestamp { get; set; } = DateTime.UtcNow;
        public int Points { get; set; } = 400;
        public bool IsOnline { get; set; } = false;
        public bool IsInGame { get; set; } = false;
        public DateTime LastSeen { get; set; } = DateTime.UtcNow;
        public string ProfilePictureUrl { get; set; } = string.Empty;

        public virtual ICollection<FriendshipRequest> SentFriendRequests { get; set; }
        public virtual ICollection<FriendshipRequest> ReceivedFriendRequests { get; set; }
        public virtual ICollection<Block> BlockedUsers { get; set; }
        public virtual ICollection<Block> BlockedByUsers { get; set; }
    }

    public class FriendshipRequest : PeriodicalModel
    {
        public Guid RequesterId { get; set; }
        public Guid ReceiverId { get; set; }
        public DateTime RequestTs { get; set; } = DateTime.UtcNow;
        public bool? IsAccepted { get; set; }

        public virtual Player Requester { get; set; }
        public virtual Player Receiver { get; set; }
    }

    public class Friendship : PeriodicalModel
    {
        public Guid Friend1Id { get; set; }
        public Guid Friend2Id { get; set; }

        public virtual Player Friend1 { get; set; }
        public virtual Player Friend2 { get; set; }
    }

    public class Block : PeriodicalModel
    {
        public Guid BlockerId { get; set; }
        public Guid BlockedId { get; set; }

        public virtual Player Blocker { get; set; }
        public virtual Player Blocked { get; set; }
    }

    public class GameRequest : PeriodicalModel
    {
        public Guid RequesterId { get; set; }
        public Guid? ReceiverId { get; set; }
        public bool? IsAccepted { get; set; }
        public bool IsPvpRequest { get; set; }

        public virtual Player Requester { get; set; }
        public virtual Player Receiver { get; set; }
        public virtual Game Game { get; set; }
    }

    public class Game : PeriodicalModel
    {
        public bool IsWhiteOnTurn { get; set; } = true;
        public Guid GameRequestId { get; set; }
        public bool IsPvp { get; set; }

        public bool? IsDraw { get; set; }
        public bool? IsWhiteWinner { get; set; }

        public virtual GameRequest GameRequest { get; set; }
        public virtual ICollection<Piece> Pieces { get; set; }
        public virtual ICollection<ApiRequest> ApiRequests { get; set; }
    }

    public class Piece
    {
        public Guid GameId { get; set; }
        [MaxLength(5)]
        public string PieceUid { get; set; } = string.Empty;
        public bool IsWhite { get; set; }
        public short PieceType { get; set; }
        public short X { get; set; }
        public short Y { get; set; }

        public virtual Game Game { get; set; }
    }

    public class ApiRequest : LoggedModel
    {
        public Guid GameId { get; set; }
        public DateTime RequestTs { get; set; } = DateTime.UtcNow;
        public Guid FromPlayerId { get; set; }
        
        [MaxLength(5)]
        public string PieceUid { get; set; } = string.Empty;
        public short X { get; set; }
        public short Y { get; set; }

        public virtual Game Game { get; set; }
        public virtual Player FromPlayer { get; set; }
        public virtual Piece Piece { get; set; }
        public virtual ApiResponse ApiResponse { get; set; }

        public bool IsSent { get; set; } = false;
    }

    public class ApiResponse : LoggedModel
    {
        public Guid ApiRequestId { get; set; }
        public string Status { get; set; }
        public string Message { get; set; }

        public virtual ApiRequest ApiRequest { get; set; }
    }
}