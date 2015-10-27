import atsapi as ats




def test(boardId):
    print boardId.value
    board = ats.boardsInSystemBySystemID(boardId.value)
