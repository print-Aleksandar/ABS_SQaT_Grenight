using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Repository.Migrations
{
    /// <inheritdoc />
    public partial class ChNameProp : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "fk_game_request_player_requested_id",
                table: "GAME_REQUEST");

            migrationBuilder.RenameColumn(
                name: "requested_id",
                table: "GAME_REQUEST",
                newName: "receiver_id");

            migrationBuilder.RenameIndex(
                name: "ix_game_request_requested_id",
                table: "GAME_REQUEST",
                newName: "ix_game_request_receiver_id");

            migrationBuilder.AddForeignKey(
                name: "fk_game_request_player_receiver_id",
                table: "GAME_REQUEST",
                column: "receiver_id",
                principalTable: "PLAYER",
                principalColumn: "id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "fk_game_request_player_receiver_id",
                table: "GAME_REQUEST");

            migrationBuilder.RenameColumn(
                name: "receiver_id",
                table: "GAME_REQUEST",
                newName: "requested_id");

            migrationBuilder.RenameIndex(
                name: "ix_game_request_receiver_id",
                table: "GAME_REQUEST",
                newName: "ix_game_request_requested_id");

            migrationBuilder.AddForeignKey(
                name: "fk_game_request_player_requested_id",
                table: "GAME_REQUEST",
                column: "requested_id",
                principalTable: "PLAYER",
                principalColumn: "id");
        }
    }
}
