def int_vec_to_bytes(intgr_arr: list[int]) -> bytearray:
    outData = bytearray()
    for intgr in intgr_arr:
        outData += intgr.to_bytes(4, 'little', signed=True)
    return outData


