library ieee;
use ieee.std_logic_1164.all;

entity test_cosim_struct_intf is
    port (
        din_valid   :  in std_logic;
        din_data    :  in std_logic_vector(7 downto 0);
        din_ready   : out std_logic;
        din_last    :  in std_logic;
        din_user    :  in std_logic;
        din_dest   :  in std_logic_vector(7 downto 0);

        dout_valid   : out std_logic;
        dout_data    : out std_logic_vector(7 downto 0);
        dout_ready   :  in std_logic;
        dout_last    : out std_logic;
        dout_user    : out std_logic;
        dout_dest   : out std_logic_vector(7 downto 0)
        );
end test_cosim_struct_intf;

architecture rtl of test_cosim_struct_intf is
begin
    dout_valid <= din_valid;
    dout_data <= din_data;
    din_ready <= dout_ready;
    dout_last <= din_last;
    dout_user <= din_user;
    dout_dest <= din_dest;
end rtl;
