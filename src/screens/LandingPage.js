import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TripTable from './triptable.js';
import { API, authHeaders } from '../api';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Modal from '@mui/material/Modal';
import TextField from '@mui/material/TextField';

const style = {
	position: 'absolute',
	top: '50%',
	left: '50%',
	transform: 'translate(-50%, -50%)',
	width: 'auto',
	bgcolor: 'background.paper',
	border: '2px solid #000',
	boxShadow: 24,
	p: 4,
};

function LandingPage() {
	let navigate = useNavigate();
	const [loggedIn, setLoggedIn] = useState(false);
	const [tripName, setTripName] = useState('');
	const [invitesCount, setInvitesCount] = useState(0);

	const [open, setOpen] = React.useState(false);

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			// console.log(authToken)
			if (!authToken) setLoggedIn(false);
			else {
				// console.log('success login');
				setLoggedIn(true);
			}
			if (localStorage.getItem('welcome')) {
				toast.success('Welcome back!');
				localStorage.removeItem('welcome');
			}
			if (localStorage.getItem('forcedLogOut')) {
				toast.error('Session Expired Login Again!');
				localStorage.removeItem('forcedLogOut');
			}
			if (localStorage.getItem('reset')) {
				toast.success('Password Reset Link sent to your email!');
				localStorage.removeItem('reset');
			}
			if (localStorage.getItem('changePass')) {
				toast.success('Password Updated!');
				localStorage.removeItem('changePass');
			}
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const login = e => {
		navigate('/login');
	};

	const signUp = e => {
		navigate('/signup');
	};

	const submitTripForm = async e => {
		e.preventDefault();
        const response = await fetch(`${API}/createtrip`, {
			method: 'POST',
            headers: authHeaders(),
			body: JSON.stringify({
				name: tripName,
			}),
		});
		const json = await response.json();
		if (!json.success) {
			json.errors.forEach(error => {
				toast.error(error.msg, {});
			});
			if (json.logout === true) {
				localStorage.removeItem('authToken');
				localStorage.setItem('forcedLogOut', true);
				navigate('/profile');
			}
		} else {
			if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
			navigate('/trip', { state: { tripid: json.tripid } });
		}
	};

	useEffect(() => {
		async function fetchInvitesCount() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) return;
			try {
				const response = await fetch(`${API}/getTripsData`, {
					method: 'GET',
					headers: authHeaders(),
				});
				const json = await response.json();
				if (json.success) setInvitesCount(json.invites || 0);
			} catch (e) {}
		}
		fetchInvitesCount();
	}, [loggedIn]);

	return (
		<div style={{ height: '100%' }}>
			{loggedIn ? (
				<div style={{ position: 'relative' }}>
					<div
						style={{
							position: 'absolute',
							top: 0,
							left: 0,
							zIndex: 1,
							width: '100%',
						}}
					>
						<TripTable />
					</div>
					<div
						className='lol'
						style={{
							position: 'absolute',
							top: 0,
							left: 0,
							zIndex: 10,
							padding: '10px',
						}}
					>
						<Button onClick={() => setOpen(true)} variant='outlined'>
							Create New Trip
						</Button>
						{invitesCount > 0 && (
							<Button onClick={() => navigate('/profile')} sx={{ ml: 1 }} variant='contained'>
								View Invites ({invitesCount})
							</Button>
						)}
						<Modal open={open} onClose={() => setOpen(false)} aria-labelledby='modal-modal-title' aria-describedby='modal-modal-description'>
							<Box sx={style}>
								<form
									onSubmit={submitTripForm}
									style={{
										width: '100%',
										display: 'flex',
										flexDirection: 'row',
										alignItems: 'stretch',
										justifyContent: 'center',
										gap: '10px',
									}}
								>
									<TextField type='text' id='tripName' value={tripName} label='Trip Name' onChange={e => setTripName(e.target.value)} />
									<Button type='submit' variant='outlined'>
										Submit
									</Button>
								</form>
							</Box>
						</Modal>
					</div>
				</div>
			) : (
				<div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%', alignItems: 'center' }}>
					<Box>
						<Typography
							variant='h4'
							style={{
								fontStyle: 'italic',
								color: '#4a4a4a',
								margin: '20px 0',
								textAlign: 'center',
								fontWeight: 'bold',
							}}
						>
							"Divide Expenses, Not Friendships."
						</Typography>
						<div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
							<Button variant='contained' onClick={login}>
								Login
							</Button>
							<Button variant='outlined' onClick={signUp} style={{ backgroundColor: 'white' }}>
								Sign Up
							</Button>
						</div>
					</Box>
				</div>
			)}
		</div>
	);
}

export default LandingPage;
