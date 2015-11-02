library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity pong is
   port
   (
      din : in std_logic_vector(31 downto 0);
      dout : in std_logic_vector(31 downto 0)
  );
end entity pong;

architecture rtl of pong is
begin
    dout <= din(23 downto 16) & din(23 downto 16) & din(7 downto 0) & din(7 downto 0);
end architecture rtl;
