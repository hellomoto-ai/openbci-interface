public class Gen24bitPatterns
{
  public static void main(String[] args)
  {
    byte[] vals = {-128, -64, -32, -16, -8, -4, -2, -1,  0, 1, 2, 4, 8, 16, 32, 64, 127};
    for (byte a : vals) {
      for (byte b : vals) {
	for (byte c : vals) {
          int val = interpret24bitAsInt32(new byte[]{a, b, c});
	  System.out.format("%d %d %d %d\n", a, b, c, val);
        }
      }
    }
  }
  public static int interpret24bitAsInt32(byte[] byteArray) {
    int newInt = (
     ((0xFF & byteArray[0]) << 16) |
     ((0xFF & byteArray[1]) << 8) |
     (0xFF & byteArray[2])
    );
    if ((newInt & 0x00800000) > 0) {
      newInt |= 0xFF000000;
    } else {
      newInt &= 0x00FFFFFF;
    }
    return newInt;
  }
}
