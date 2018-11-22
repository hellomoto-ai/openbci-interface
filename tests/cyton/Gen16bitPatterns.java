public class Gen16bitPatterns
{
  public static void main(String[] args)
  {
    byte[] vals = {-128, -64, -32, -16, -8, -4, -2, -1,  0, 1, 2, 4, 8, 16, 32, 64, 127};
    for (byte a : vals) {
      for (byte b : vals) {
        int val = interpret16bitAsInt32(new byte[]{a, b});
        System.out.format("%d %d %d\n", a, b, val);
      }
    }
  }
  public static int interpret16bitAsInt32(byte[] byteArray) {
    int newInt = (
      ((0xFF & byteArray[0]) << 8) |
       (0xFF & byteArray[1])
      );
    if ((newInt & 0x00008000) > 0) {
          newInt |= 0xFFFF0000;
    } else {
          newInt &= 0x0000FFFF;
    }
    return newInt;
  }
}
