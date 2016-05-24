library ieee;
use ieee.std_logic_1164.all;

entity test_cosim_struct_intf is
    port (
        din_valid   :  in std_logic;
        din_data    :  in std_logic_vector(7 downto 0);
        din_user    :  in std_logic;
        din_ready   : out std_logic;
        din_last    :  in std_logic
        );
end test_cosim_struct_intf;

architecture rtl of test_cosim_struct_intf is
begin
    din_ready <= '1';
end rtl;
