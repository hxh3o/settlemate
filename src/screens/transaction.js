import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { API, authHeaders } from '../api';

import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { Table, TableHead, TableBody, TableCell, TableContainer, TableRow, Paper } from '@mui/material';

function Transaction() {
	let navigate = useNavigate();
	let location = useLocation();
	const [content, setContent] = useState(0);
	const [name, setName] = useState('');
	const [desc, setDesc] = useState('');
	const [amt, setAmt] = useState(-1);
	const [checked, setChecked] = useState([]);
	const [bill, setBill] = useState('');
	const [transactionEnabled, setTransactionEnabled] = useState('Enabled');
	const [owner, setOwner] = useState({ name: '', email: '', _id: '' });
	const [memmap, setMap] = useState({});
	const [myId, setMyId] = useState(null);
	const [amtDist, setAmtDist] = useState({});
	const [tripOwner, setTripOwner] = useState('');

	useEffect(() => {
		async function authorize() {
			const authToken = localStorage.getItem('authToken');
			if (!authToken) navigate('/profile');
			else fetchData();
		}
		async function fetchData() {
			try {
                const response = await fetch(`${API}/getTransactionData`, {
					method: 'POST',
                    headers: authHeaders(),
					body: JSON.stringify({
						tripid: location.state.tripid,
						transactionid: location.state.transactionid,
					}),
				});
				const json = await response.json();
				// console.log(json);
				if (!json.success) {
					json.errors.forEach(error => {
						toast.error(error.msg, {});
					});
					if (json.logout === true) {
						localStorage.removeItem('authToken');
						localStorage.setItem('forcedLogOut', true);
						navigate('/');
					}
				} else {
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
					console.log(json);
					setAmt(json.amt);
					setDesc(json.desc);
					setName(json.name);
					setBill(json.bill);
					setChecked(json.damg);
					setMap(json.memmap);
					setAmtDist(json.damgmap);
					setOwner(json.owner);
					setMyId(json.myId);
					if (json.switchVal) setTransactionEnabled('Enabled');
					else setTransactionEnabled('Disabled');
					setTripOwner(json.tripOwner);
				}
			} catch (error) {
				console.error('Error fetching data :', error);
			}
		}
		authorize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	return (
		<div>
			<div
				style={{
					display: 'flex',
					justifyContent: 'center',
					paddingTop: '10px',
					gap: '10px',
				}}
			>
				<Button
					variant='contained'
					onClick={() =>
						navigate('/transactions', {
							state: {
								tripid: location.state.tripid,
							},
						})
					}
				>
					Back To Transactions
				</Button>
				<Button
					variant='contained'
					onClick={() =>
						navigate('/trip', {
							state: {
								tripid: location.state.tripid,
							},
						})
					}
				>
					Back To Trip
				</Button>
				{(myId === owner._id || myId === tripOwner) && (
					<Button
						variant='contained'
						onClick={() =>
							navigate('/edittransaction', {
								state: {
									tripid: location.state.tripid,
									transactionid: location.state.transactionid,
								},
							})
						}
					>
						Edit Transaction
					</Button>
				)}
			</div>
			{content === 0 && (
				<div
					style={{
						display: 'flex',
						flexDirection: 'column',
						gap: '10px',
					}}
				>
					<div
						style={{
							display: 'flex',
							gap: '40px',
							justifyContent: 'center',
							paddingTop: '20px',
						}}
					>
						<Typography variant='h4'>{name}</Typography>
					</div>
					<div
						style={{
							display: 'flex',
							gap: '40px',
							justifyContent: 'center',
							paddingTop: '20px',
						}}
					>
						<Typography variant='h5'>
							Managed By : {owner.name} &nbsp;&nbsp;{owner.email}
						</Typography>
					</div>
					<div
						style={{
							display: 'flex',
							gap: '40px',
							justifyContent: 'center',
						}}
					>
						<Typography variant='h5'>Transaction Status : {transactionEnabled}</Typography>
					</div>
					<div
						style={{
							display: 'flex',
							justifyContent: 'center',
							gap: '10px',
						}}
					>
						<Typography variant='h5'>Bill Amount : {amt}</Typography>
						{bill.length > 0 && (
							<Button variant='outlined' onClick={() => window.open(`https://drive.google.com/uc?export=view&id=${bill}`, '_blank')}>
								View bill Image
							</Button>
						)}
					</div>
					<div
						style={{
							padding: '10px',
							display: 'flex',
							flexDirection: 'column',
							justifyContent: 'center',
							width: '100%',
							alignItems: 'center',
						}}
					>
						<Typography variant='h6' style={{ width: '50%', textAlign: 'center' }}>
							Description
						</Typography>
						<Typography variant='h6' style={{ width: '50%', textAlign: 'center' }}>
							{desc}
						</Typography>
					</div>
					<div
						style={{
							display: 'flex',
							justifyContent: 'center',
						}}
					>
						<Button variant='contained' onClick={() => setContent(1)}>
							Next
						</Button>
					</div>
				</div>
			)}
			{content === 1 && (
				<div
					style={{
						display: 'flex',
						flexDirection: 'column',
						justifyContent: 'center',
						alignItems: 'center',
					}}
				>
					<div style={{ width: '50%', height: '50vh' }}>
						<TableContainer component={Paper}>
							<Table>
								<TableHead>
									<TableRow>
										<TableCell>Name</TableCell>
										<TableCell>Email</TableCell>
										<TableCell>Amount</TableCell>
									</TableRow>
								</TableHead>
								<TableBody>
									{checked.map((item, index) => (
										<TableRow key={index}>
											<TableCell>{memmap[item].name}</TableCell>
											<TableCell>{memmap[item].email}</TableCell>
											<TableCell>{amtDist[item]}</TableCell>
										</TableRow>
									))}
								</TableBody>
							</Table>
						</TableContainer>
					</div>
					<div
						style={{
							padding: '10px',
							display: 'flex',
							justifyContent: 'center',
							gap: '10px',
						}}
					>
						<Button variant='contained' onClick={() => setContent(0)}>
							Prev
						</Button>
					</div>
				</div>
			)}
		</div>
	);
}

export default Transaction;
