using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Repository.Migrations
{
    /// <inheritdoc />
    public partial class ChangeGameReqNotNull : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "fk_game_game_request_game_request_id",
                table: "GAME");

            migrationBuilder.AlterColumn<Guid>(
                name: "game_request_id",
                table: "GAME",
                type: "uuid",
                nullable: false,
                defaultValue: new Guid("00000000-0000-0000-0000-000000000000"),
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddForeignKey(
                name: "fk_game_game_request_game_request_id",
                table: "GAME",
                column: "game_request_id",
                principalTable: "GAME_REQUEST",
                principalColumn: "id",
                onDelete: ReferentialAction.Cascade);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "fk_game_game_request_game_request_id",
                table: "GAME");

            migrationBuilder.AlterColumn<Guid>(
                name: "game_request_id",
                table: "GAME",
                type: "uuid",
                nullable: true,
                oldClrType: typeof(Guid),
                oldType: "uuid");

            migrationBuilder.AddForeignKey(
                name: "fk_game_game_request_game_request_id",
                table: "GAME",
                column: "game_request_id",
                principalTable: "GAME_REQUEST",
                principalColumn: "id");
        }
    }
}
