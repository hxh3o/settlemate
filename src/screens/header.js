import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import { API, authHeaders } from '../api';

function Header() {
	const [loggedIn, setLoggedIn] = useState(false);
	const [userName, setUserName] = useState('Loading...');
	const navigate = useNavigate();
	const [anchorEl, setAnchorEl] = React.useState(null);
	const open = Boolean(anchorEl);
	const handleClick = event => {
		setAnchorEl(event.currentTarget);
	};
	const handleClose = () => {
		setAnchorEl(null);
	};

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			// console.log(authToken)
			if (!authToken) setLoggedIn(false);
			else {
				// console.log('success login');
				fetchData();
				setLoggedIn(true);
			}
		}
        async function fetchData() {
			try {
                const response = await fetch(`${API}/getUserData`, {
                    method: 'GET',
                    headers: authHeaders(),
                });
				const json = await response.json();
				if (json.success) {
                    setUserName(json.data.name);
					// console.log(json.data);
				} else {
					console.log(json.errors);
					if (json.logout === true) {
						localStorage.removeItem('authToken');
						localStorage.setItem('forcedLogOut', true);
						navigate('/profile');
					}
				}
			} catch (error) {
				console.error('Error fetching userData :', error);
			}
		}
		authorize();
	}, [navigate]);

	const logout = () => {
		handleClose();
		console.log('trying logout');
		localStorage.removeItem('authToken');
		setLoggedIn(false);
		navigate('/login');
	};

	const profile = () => {
		handleClose();
		navigate('/profile');
	};

	return (
		<div className='headerBox'>
			<div className='logo' onClick={() => navigate('/')}>
				SettleMate
			</div>
			{loggedIn && (
				<div
					style={{
						display: 'flex',
						justifyContent: 'end',
						width: '50%',
						paddingRight: '20px',
					}}
				>
					<Button
						id='basic-button'
						aria-controls={open ? 'basic-menu' : undefined}
						aria-haspopup='true'
						aria-expanded={open ? 'true' : undefined}
						onClick={handleClick}
						style={{
							color: 'white',
							border: '1px solid white',
							height: '80%',
						}}
					>
						{userName}
					</Button>
					<Menu
						id='basic-menu'
						anchorEl={anchorEl}
						open={open}
						onClose={handleClose}
						MenuListProps={{
							'aria-labelledby': 'basic-button',
						}}
					>
						<MenuItem onClick={profile}>Dashboard</MenuItem>
						<MenuItem onClick={logout}>Logout</MenuItem>
					</Menu>
				</div>
			)}
		</div>
	);
}

export default Header;
